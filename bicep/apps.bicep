targetScope = 'resourceGroup'

@description('Base name used to derive resource names (must match main.bicep deployment)')
param appName string = 'sage'

@description('Deployment environment suffix (must match main.bicep deployment)')
param envName string = 'dev'

@description('Primary Azure region')
param location string = resourceGroup().location

@description('Name of the existing Container Registry (from main.bicep output acrName)')
param acrName string

@description('Name of the existing Azure OpenAI account (from main.bicep output openAiAccountName)')
param openAiAccountName string

@description('Name of the existing Azure Voice Live (Foundry AIServices) account (from main.bicep output voiceLiveAccountName)')
param voiceLiveAccountName string

@description('Name of the existing Storage account (from main.bicep output storageAccountName)')
param storageAccountName string

@description('Resource ID of the existing Container Apps environment (from main.bicep output environmentId)')
param environmentId string

@description('Resource ID of the user-assigned managed identity used for ACR pull (from main.bicep output acrPullIdentityId)')
param acrPullIdentityId string

@description('Chat model deployment name (must match what was deployed in main.bicep)')
param chatModelName string = 'gpt-4.1'

@description('Realtime voice model deployment name (must match what was deployed in main.bicep)')
param realtimeModelName string = 'gpt-realtime'

@description('Full backend container image reference in ACR, e.g. myacr.azurecr.io/sage-backend:tag')
param backendImage string

@description('Full frontend container image reference in ACR, e.g. myacr.azurecr.io/sage-frontend:tag')
param frontendImage string

@description('Allowed CORS origin for the backend (set to the frontend FQDN once known)')
param corsOrigins string = '*'

var resourceToken = '${appName}-${envName}'
var tags = {
  'azd-env-name': envName
  app: appName
}

resource acrExisting 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource openAiExisting 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiAccountName
}

resource voiceLiveExisting 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: voiceLiveAccountName
}

resource storageExisting 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

module backendApp 'modules/containerapp-backend.bicep' = {
  name: 'backend-app'
  params: {
    name: '${resourceToken}-backend'
    location: location
    tags: tags
    environmentId: environmentId
    image: backendImage
    acrLoginServer: acrExisting.properties.loginServer
    useAcrRegistry: true
    acrPullIdentityId: acrPullIdentityId
    openAiEndpoint: openAiExisting.properties.endpoint
    voiceLiveEndpoint: voiceLiveExisting.properties.endpoint
    chatModelDeploymentName: chatModelName
    realtimeModelDeploymentName: realtimeModelName
    storageConnectionString: 'DefaultEndpointsProtocol=https;AccountName=${storageExisting.name};AccountKey=${storageExisting.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
    corsOrigins: corsOrigins
  }
}

module frontendApp 'modules/containerapp-frontend.bicep' = {
  name: 'frontend-app'
  params: {
    name: '${resourceToken}-frontend'
    location: location
    tags: tags
    environmentId: environmentId
    image: frontendImage
    acrLoginServer: acrExisting.properties.loginServer
    useAcrRegistry: true
    acrPullIdentityId: acrPullIdentityId
  }
}

module rbac 'modules/rbac-openai.bicep' = {
  name: 'rbac-openai'
  params: {
    backendPrincipalId: backendApp.outputs.principalId
    openAiId: openAiExisting.id
  }
}

module rbacVoiceLive 'modules/rbac-voicelive.bicep' = {
  name: 'rbac-voicelive'
  params: {
    backendPrincipalId: backendApp.outputs.principalId
    voiceLiveId: voiceLiveExisting.id
  }
}

output backendFqdn string = backendApp.outputs.fqdn
output frontendFqdn string = frontendApp.outputs.fqdn
output backendAppName string = backendApp.outputs.name
output frontendAppName string = frontendApp.outputs.name
