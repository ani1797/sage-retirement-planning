# Azure Deployment Guide (Bicep, single resource group)

This guide deploys **Sage Retirement Planning** end-to-end to Azure using Bicep — one
resource group contains everything the app needs, and a single script builds images,
provisions infrastructure, and gives you a working real-time UI URL.

This deployment has been executed end-to-end against a real Azure subscription and
verified working: live chat with tool-calling, streaming scenario projections, and the
realtime voice WebSocket all confirmed functional against the deployed backend.

## Architecture

```
Resource Group (e.g. sage-retirement-rg, region: eastus2)
│
├── Log Analytics workspace ──────► Container Apps environment logs
│
├── Container Apps Environment
│   ├── Frontend Container App (Next.js, external ingress :3847)
│   └── Backend Container App  (FastAPI, external ingress :8172, WebSocket voice)
│
├── Azure Container Registry (Basic SKU)
│   ├── sage-frontend:<tag>
│   └── sage-backend:<tag>
│
├── Azure OpenAI account (Cognitive Services, kind=OpenAI)
│   ├── Deployment: gpt-4.1 (chat / scenario reasoning, via Chat Completions API)
│   └── Deployment: gpt-realtime (voice mode)
│
├── User-assigned managed identity (ACR pull) ──► granted AcrPull in phase 1
│
└── Storage account (Blob) ───────► conversations & saved scenarios
```

### Two-phase Bicep deployment

Infrastructure and apps are split into **two templates**, deployed in sequence:

- **`bicep/main.bicep`** (infra-only) — Log Analytics, ACR, Azure OpenAI (both model
  deployments), Storage, the Container Apps environment, and a **user-assigned managed
  identity** that is granted `AcrPull` immediately (in this same phase, well before any
  Container App exists).
- **`bicep/apps.bicep`** (apps-only) — looks up the phase-1 resources via `existing` and
  deploys the backend/frontend Container Apps directly with **real** ACR image tags,
  plus the backend's `Cognitive Services OpenAI User` role assignment.

This two-phase split (rather than one template using a placeholder image, then
redeploying) exists for two reasons, both discovered while validating this guide against
a live subscription:
1. A placeholder image (e.g. `mcr.microsoft.com/k8se/quickstart:latest`) doesn't listen
   on the app's configured target port, so Container Apps ingress readiness never
   succeeds and the ARM deployment times out ("Operation expired").
2. Granting `AcrPull` to a Container App's *system-assigned* identity in the same
   deployment that also configures the image pull creates a race — the pull can be
   attempted before the role assignment propagates. Using a **user-assigned** identity
   created and RBAC'd in phase 1 (minutes before phase 2 apps reference it) avoids this
   entirely.

Both Container Apps also use **system-assigned** identities for their own RBAC:
- Backend → `Cognitive Services OpenAI User` on the Azure OpenAI account (no API keys,
  `DefaultAzureCredential` end-to-end).
- Both apps → the user-assigned identity above for `AcrPull`.

The Storage connection string is passed to the backend as a Container Apps **secret**
(encrypted, not visible in plaintext in the portal) since the app's blob storage backend
only supports connection-string auth today.

## Prerequisites

- Azure subscription with access to deploy Azure OpenAI (`gpt-4.1` and, for voice,
  `gpt-realtime` — check model availability by region if you change the default region;
  the deprecated `gpt-4o-realtime-preview` model has been retired and is no longer
  deployable in most regions — use `gpt-realtime` instead).
- Azure CLI >= 2.60, logged in (`az login`) with the right subscription selected
  (`az account set --subscription <id>`).
- No local Docker needed — images are built remotely with `az acr build`.

## Deploy

```bash
chmod +x bicep/scripts/deploy.sh bicep/scripts/teardown.sh

# Usage: ./bicep/scripts/deploy.sh [resource-group-name] [location]
./bicep/scripts/deploy.sh sage-retirement-rg eastus2
```

This runs in three phases automatically:
1. **Infra** (`main.bicep`) — deploys every non-app resource (ACR, Azure OpenAI,
   Storage, Log Analytics, Container Apps environment, ACR-pull identity + RBAC).
2. **Build images** — `az acr build` compiles the backend and frontend Docker images
   directly inside ACR, baking the backend's predicted live URL into the frontend build
   (`NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL`).
3. **Deploy apps** (`apps.bicep`) — deploys the backend/frontend Container Apps with the
   real image tags from step 2 and the pre-granted ACR-pull identity.

At the end you'll get:
```
Frontend URL: https://sage-dev-frontend.<region>.azurecontainerapps.io
Backend URL:  https://sage-dev-backend.<region>.azurecontainerapps.io
```

Open the **Frontend URL** — the UI is fully live (real Azure OpenAI-backed chat,
scenario projections, and voice mode), no mock mode.

**Redeploying after any change:** because infrastructure changes must only be made via
Bicep (never `az containerapp update`/other direct mutations), any code change requires
rebuilding the affected image with `az acr build` and redeploying `apps.bicep` with the
new image tag as a parameter. `main.bicep` only needs to be redeployed if the shared
infra itself changes (models, SKUs, environment settings).

## Customizing

Edit `bicep/main.parameters.json` or pass `--parameters key=value` overrides:

| Parameter | Default | Notes |
|---|---|---|
| `appName` | `sage` | Prefix for all resource names |
| `envName` | `dev` | Suffix (e.g. `dev`, `staging`, `prod`) |
| `location` | `eastus2` | Region for Container Apps, ACR, Storage, Log Analytics, Azure OpenAI |
| `chatModelName` / `chatModelVersion` | `gpt-4.1` / `2025-04-14` | Chat model deployment |
| `realtimeModelName` / `realtimeModelVersion` | `gpt-realtime` / `2025-08-28` | Voice model deployment |

Re-running `deploy.sh` is safe — it always redeploys idempotently and rebuilds fresh
image tags.

## Tear down

```bash
./bicep/scripts/teardown.sh sage-retirement-rg
```

Deletes the entire resource group (all resources, no leftovers) after a confirmation
prompt.

## Cost notes

- Container Apps: consumption plan, scales to zero when idle (only the `minReplicas: 1`
  keeps 1 instance warm — lower to `0` in the modules if you want cold-start savings).
- ACR: Basic SKU (cheapest tier, sufficient for a couple of images).
- Azure OpenAI: pay-as-you-go per token; the realtime voice model has its own per-minute
  billing.
- Storage account: Standard_LRS, negligible for JSON blob storage.

## Security notes / follow-ups

- **No authentication layer** — both apps are deployed with public ingress, matching the
  current app (there's no login code). Anyone with the URL can use it. For a shared or
  production deployment, consider:
  - Container Apps built-in authentication (Easy Auth) with Microsoft Entra ID
  - IP restrictions via Container Apps ingress rules
- Backend CORS currently defaults to allow all origins in `main.py` regardless of the
  `CORS_ORIGINS` env var set by this deployment (pre-existing app behavior) — the Bicep
  sets the variable for forward-compatibility if that's tightened in code later.
- Storage credentials are stored as a Container Apps secret; for stricter secret
  management, route it through Azure Key Vault + `Microsoft.App/containerApps` Key Vault
  references.

## Application fixes made to enable this deployment

A few pre-existing issues in the app code blocked a fully working deployment and were
fixed as part of validating this guide (all outside the Bicep/infra layer):

- **Azure OpenAI Assistants API retirement** — `backend/main.py` used the Assistants
  API (`client.beta.assistants`/`threads`/`runs`), which Azure has fully retired
  (HTTP 410, "Follow the migration guide..."). This broke every chat and scenario
  endpoint. Migrated to the standard **Chat Completions API** (`client.chat.completions`)
  with an equivalent in-memory conversation/thread store and the same function-calling
  (tool use) and streaming behavior — no endpoint contracts changed.
- **Missing `openai`/`azure-storage-blob` dependencies** — `backend/pyproject.toml` only
  pulled in `openai` transitively via the optional `eval` extra, so the production
  install (`uv sync --frozen --no-dev`) never installed it, crash-looping the backend
  container. Added both as direct dependencies.
- **pnpm build-script sandboxing** — pnpm v10+ blocks native build scripts (e.g. `sharp`)
  by default, breaking the frontend Docker build. Pinned `pnpm@9` in the root
  `Dockerfile` to match the committed `pnpm-lock.yaml` (`lockfileVersion: '9.0'`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `main.bicep` fails with a quota/model error | Your subscription may lack quota for `gpt-4.1` or `gpt-realtime` in the chosen region — try a different `location`, request quota, or change `chatModelName`/`realtimeModelName`. |
| `az acr build` fails with `tarfile: unsupported type` | A live git file (e.g. `.git/fsmonitor--daemon.ipc`) is breaking the build-context tar. Build from a clean copy instead: `rsync -a --exclude .git --exclude node_modules --exclude .next "$(pwd)/" /tmp/build-ctx/ && az acr build ... /tmp/build-ctx`. |
| `az acr build` (frontend) fails with `ERR_PNPM_IGNORED_BUILDS` | Make sure the Dockerfile pins `pnpm@9` (already fixed in this repo's `Dockerfile`). |
| Frontend loads but chat fails | Check backend logs: `az containerapp logs show -n <backend-app-name> -g <rg> --tail 100`. Look for `ModuleNotFoundError` (dependency issue — rebuild the image) or `assistants_api_deprecated` (means an older backend image predating the Chat Completions migration is still deployed — rebuild and redeploy `apps.bicep`). |
| Voice mode doesn't connect | Confirm the realtime model deployed successfully (`az cognitiveservices account deployment list --name <openai-account> -g <rg>`) and that `realtimeModelName` matches an available, non-deprecated model in your region. |
