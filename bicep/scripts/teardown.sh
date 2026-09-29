#!/usr/bin/env bash
# ============================================================================
# Sage Retirement Planning - spin down / delete all Azure resources
# ============================================================================
# Deletes the entire resource group created by deploy.sh, removing every
# resource (Container Apps, ACR, Azure OpenAI, Storage, Log Analytics).
#
# Usage:
#   ./bicep/scripts/teardown.sh [resource-group-name]
# ============================================================================
set -euo pipefail

RESOURCE_GROUP="${1:-sage-retirement-rg}"

echo "This will permanently delete resource group '${RESOURCE_GROUP}' and ALL resources in it."
read -r -p "Type the resource group name to confirm: " CONFIRM
if [[ "${CONFIRM}" != "${RESOURCE_GROUP}" ]]; then
  echo "Confirmation did not match. Aborting."
  exit 1
fi

echo "==> Deleting resource group '${RESOURCE_GROUP}'..."
az group delete --name "${RESOURCE_GROUP}" --yes --no-wait

echo "Deletion started (running in background on Azure). Check status with:"
echo "  az group show --name ${RESOURCE_GROUP}"
