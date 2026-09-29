#!/usr/bin/env bash
# ============================================================================
# Sage Retirement Planning - end-to-end Azure deployment
# ============================================================================
# Creates a single resource group with everything the app needs and deploys
# the frontend + backend as Container Apps, using two Bicep templates:
#
#   main.bicep  (infra-only) - Log Analytics, ACR, Azure OpenAI (chat +
#               realtime voice model deployments), Storage, Container Apps
#               environment, and a user-assigned managed identity that is
#               granted AcrPull well before any Container App references it
#               (avoids an RBAC-propagation race).
#   apps.bicep  (apps-only)  - looks up the phase-1 resources via `existing`
#               and deploys the backend/frontend Container Apps directly
#               with real ACR images (no placeholder image is ever used,
#               since a placeholder that doesn't listen on the configured
#               target port makes Container Apps ingress readiness hang and
#               the deployment time out).
#
# Usage:
#   ./bicep/scripts/deploy.sh [resource-group-name] [location]
#
# Requires: az CLI logged in (az login), Bicep CLI extension (auto-installed).
# No local Docker needed - images are built remotely with `az acr build`.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BICEP_DIR="${REPO_ROOT}/bicep"

RESOURCE_GROUP="${1:-sage-retirement-rg}"
LOCATION="${2:-eastus2}"
APP_NAME="${APP_NAME:-sage}"
ENV_NAME="${ENV_NAME:-dev}"
CHAT_MODEL_NAME="${CHAT_MODEL_NAME:-gpt-4.1}"
REALTIME_MODEL_NAME="${REALTIME_MODEL_NAME:-gpt-realtime}"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"

echo "==> Checking Azure CLI login..."
az account show >/dev/null 2>&1 || { echo "Not logged in. Run 'az login' first."; exit 1; }
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "    Subscription: ${SUBSCRIPTION_ID}"

echo "==> Ensuring resource group '${RESOURCE_GROUP}' exists in '${LOCATION}'..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" -o none

echo ""
echo "==================================================================="
echo " Phase 1/3: Deploying infrastructure (main.bicep, no apps yet)"
echo "==================================================================="
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "sage-infra-${TIMESTAMP}" \
  --template-file "${BICEP_DIR}/main.bicep" \
  --parameters appName="${APP_NAME}" envName="${ENV_NAME}" location="${LOCATION}" \
  --parameters chatModelName="${CHAT_MODEL_NAME}" realtimeModelName="${REALTIME_MODEL_NAME}" \
  -o none

INFRA_OUTPUTS=$(az deployment group show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "sage-infra-${TIMESTAMP}" \
  --query properties.outputs -o json)

ACR_NAME=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['acrName']['value'])")
ACR_LOGIN_SERVER=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['acrLoginServer']['value'])")
OPENAI_ACCOUNT_NAME=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['openAiAccountName']['value'])")
VOICE_LIVE_ACCOUNT_NAME=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['voiceLiveAccountName']['value'])")
STORAGE_ACCOUNT_NAME=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['storageAccountName']['value'])")
ENVIRONMENT_ID=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['environmentId']['value'])")
ENVIRONMENT_NAME=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['environmentName']['value'])")
ACR_PULL_IDENTITY_ID=$(echo "${INFRA_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['acrPullIdentityId']['value'])")

echo "    ACR: ${ACR_LOGIN_SERVER}"
echo "    Azure OpenAI account: ${OPENAI_ACCOUNT_NAME}"
echo "    Azure Voice Live account: ${VOICE_LIVE_ACCOUNT_NAME}"

# Predict the backend FQDN so it can be baked into the frontend build
# (Container Apps environment default domain + app name is deterministic).
DEFAULT_DOMAIN=$(az containerapp env show --name "${ENVIRONMENT_NAME}" --resource-group "${RESOURCE_GROUP}" --query properties.defaultDomain -o tsv)
BACKEND_FQDN="${APP_NAME}-${ENV_NAME}-backend.${DEFAULT_DOMAIN}"
BACKEND_URL="https://${BACKEND_FQDN}"
BACKEND_WS_URL="wss://${BACKEND_FQDN}"

echo ""
echo "==================================================================="
echo " Phase 2/3: Building container images in ACR"
echo "==================================================================="
IMAGE_TAG="${TIMESTAMP}"
BACKEND_IMAGE="${ACR_LOGIN_SERVER}/sage-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${ACR_LOGIN_SERVER}/sage-frontend:${IMAGE_TAG}"

echo "==> Building backend image: ${BACKEND_IMAGE}"
az acr build \
  --registry "${ACR_NAME}" \
  --image "sage-backend:${IMAGE_TAG}" \
  --file "${REPO_ROOT}/backend/Dockerfile" \
  "${REPO_ROOT}/backend"

# NOTE: az acr build tars up the build context locally before uploading. If
# the repo root contains a live git fsmonitor socket (.git/fsmonitor--daemon.ipc)
# the tar step can fail with "unsupported type" even though .dockerignore
# excludes .git. Build from a clean copy without .git/node_modules/.next if
# you hit that error, e.g.:
#   rsync -a --exclude .git --exclude node_modules --exclude .next "${REPO_ROOT}/" /tmp/frontend-build/
#   az acr build ... /tmp/frontend-build
echo "==> Building frontend image: ${FRONTEND_IMAGE} (backend URL baked in: ${BACKEND_URL})"
az acr build \
  --registry "${ACR_NAME}" \
  --image "sage-frontend:${IMAGE_TAG}" \
  --file "${REPO_ROOT}/Dockerfile" \
  --build-arg NEXT_PUBLIC_API_URL="${BACKEND_URL}" \
  --build-arg NEXT_PUBLIC_WS_URL="${BACKEND_WS_URL}" \
  --build-arg NEXT_PUBLIC_APP_ENV=production \
  "${REPO_ROOT}"

echo ""
echo "==================================================================="
echo " Phase 3/3: Deploying Container Apps with real images (apps.bicep)"
echo "==================================================================="
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "sage-apps-${TIMESTAMP}" \
  --template-file "${BICEP_DIR}/apps.bicep" \
  --parameters appName="${APP_NAME}" envName="${ENV_NAME}" location="${LOCATION}" \
  --parameters acrName="${ACR_NAME}" openAiAccountName="${OPENAI_ACCOUNT_NAME}" voiceLiveAccountName="${VOICE_LIVE_ACCOUNT_NAME}" storageAccountName="${STORAGE_ACCOUNT_NAME}" \
  --parameters environmentId="${ENVIRONMENT_ID}" acrPullIdentityId="${ACR_PULL_IDENTITY_ID}" \
  --parameters chatModelName="${CHAT_MODEL_NAME}" realtimeModelName="${REALTIME_MODEL_NAME}" \
  --parameters backendImage="${BACKEND_IMAGE}" frontendImage="${FRONTEND_IMAGE}" \
  --parameters corsOrigins="*" \
  -o none

APPS_OUTPUTS=$(az deployment group show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "sage-apps-${TIMESTAMP}" \
  --query properties.outputs -o json)

FRONTEND_FQDN=$(echo "${APPS_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['frontendFqdn']['value'])")
BACKEND_FQDN=$(echo "${APPS_OUTPUTS}" | python3 -c "import json,sys; print(json.load(sys.stdin)['backendFqdn']['value'])")

echo ""
echo "==> Waiting for backend health check..."
for i in $(seq 1 20); do
  if curl -sf "https://${BACKEND_FQDN}/health" >/dev/null 2>&1; then
    echo "    Backend healthy."
    break
  fi
  echo "    Waiting for backend... (${i}/20)"
  sleep 10
done

echo ""
echo "==================================================================="
echo " Deployment complete!"
echo "==================================================================="
echo " Frontend URL: https://${FRONTEND_FQDN}"
echo " Backend URL:  https://${BACKEND_FQDN}"
echo " Resource Group: ${RESOURCE_GROUP}"
echo ""
echo " Open the Frontend URL in your browser to use the app in real-time mode."
echo " To redeploy after a code change: rebuild the relevant image with"
echo " 'az acr build' and rerun 'az deployment group create' against apps.bicep"
echo " with the new image tag (never mutate the Container App directly)."
echo " To tear everything down: ./bicep/scripts/teardown.sh ${RESOURCE_GROUP}"
echo "==================================================================="
