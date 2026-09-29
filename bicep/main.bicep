targetScope = 'resourceGroup'

@description('Base name used to derive resource names (lowercase alphanumeric, no spaces)')
@minLength(3)
@maxLength(16)
param appName string = 'sage'

@description('Deployment environment suffix (dev, staging, prod)')
param envName string = 'dev'

@description('Primary Azure region for most resources')
param location string = resourceGroup().location

@description('Azure region for the OpenAI account (must support gpt-4.1 / gpt-4o-realtime-preview)')
param openAiLocation string = location

@description('Chat model name')
param chatModelName string = 'gpt-4.1'

@description('Chat model version')
param chatModelVersion string = '2025-04-14'

@description('Whether to deploy the realtime voice model')
param deployRealtimeModel bool = true

@description('Realtime voice model name')
param realtimeModelName string = 'gpt-realtime'

@description('Realtime voice model version')
param realtimeModelVersion string = '2025-08-28'

// Short unique suffix so globally-unique resources (ACR, Storage, Cognitive Services
// custom subdomain) don't collide with other deployments/subscriptions.
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var resourceToken = '${appName}-${envName}'
var tags = {
  'azd-env-name': envName
  app: appName
}

module logAnalytics 'modules/loganalytics.bicep' = {
  name: 'loganalytics'
  params: {
    name: '${resourceToken}-logs'
    location: location
    tags: tags
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: replace('${appName}${envName}acr${uniqueSuffix}', '-', '')
    location: location
    tags: tags
  }
}

module openAi 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    name: '${resourceToken}-openai-${uniqueSuffix}'
    location: openAiLocation
    tags: tags
    chatModelName: chatModelName
    chatModelVersion: chatModelVersion
  }
}

// Azure Voice Live requires a Microsoft Foundry (AIServices-kind) account - the
// Voice Live WebSocket endpoint isn't served by a plain Azure OpenAI account.
module voiceLive 'modules/voicelive.bicep' = if (deployRealtimeModel) {
  name: 'voicelive'
  params: {
    name: '${resourceToken}-voicelive-${uniqueSuffix}'
    location: openAiLocation
    tags: tags
    realtimeModelName: realtimeModelName
    realtimeModelVersion: realtimeModelVersion
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: replace('${appName}${envName}st${uniqueSuffix}', '-', '')
    location: location
    tags: tags
  }
}

module acaEnv 'modules/containerapps-env.bicep' = {
  name: 'aca-env'
  params: {
    name: '${resourceToken}-env'
    location: location
    tags: tags
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsSharedKey: logAnalytics.outputs.sharedKey
  }
}

// User-assigned identity dedicated to ACR pulls. Creating it (and granting AcrPull)
// here in phase 1 - well before the Container Apps are created in phase 2/apps.bicep -
// avoids the RBAC-propagation race that occurs when a system-assigned identity is
// granted access in the same deployment that also tries to pull the image.
module acrPullIdentity 'modules/identity.bicep' = {
  name: 'acr-pull-identity'
  params: {
    name: '${resourceToken}-acrpull-id'
    location: location
    tags: tags
  }
}

module acrPullRbac 'modules/rbac-acrpull.bicep' = {
  name: 'acr-pull-rbac'
  params: {
    principalId: acrPullIdentity.outputs.principalId
    acrId: acr.outputs.registryId
  }
}

output acrLoginServer string = acr.outputs.loginServer
output acrName string = acr.outputs.registryName
output acrId string = acr.outputs.registryId
output openAiEndpoint string = openAi.outputs.endpoint
output openAiAccountName string = openAi.outputs.accountName
output openAiId string = openAi.outputs.accountId
output voiceLiveEndpoint string = deployRealtimeModel ? voiceLive.outputs.endpoint : ''
output voiceLiveAccountName string = deployRealtimeModel ? voiceLive.outputs.accountName : ''
output voiceLiveId string = deployRealtimeModel ? voiceLive.outputs.accountId : ''
output storageAccountName string = storage.outputs.storageAccountName
output environmentId string = acaEnv.outputs.environmentId
output environmentName string = acaEnv.outputs.environmentName
output acrPullIdentityId string = acrPullIdentity.outputs.identityId
