@description('Name of the backend Container App')
param name string

@description('Azure region')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Container Apps environment resource ID')
param environmentId string

@description('Full container image reference, e.g. myacr.azurecr.io/sage-backend:tag')
param image string

@description('ACR login server (used to configure the registry on the app)')
param acrLoginServer string

@description('Whether to configure ACR pull credentials (skip for public placeholder images so the app does not wait on RBAC propagation)')
param useAcrRegistry bool = false

@description('Resource ID of the user-assigned managed identity used for ACR pull (must already have AcrPull granted)')
param acrPullIdentityId string = ''

@description('Azure OpenAI endpoint')
param openAiEndpoint string

@description('Azure Voice Live (Foundry AIServices) endpoint')
param voiceLiveEndpoint string

@description('Chat model deployment name')
param chatModelDeploymentName string

@description('Realtime voice model deployment name')
param realtimeModelDeploymentName string

@description('Storage connection string for conversation/scenario persistence')
@secure()
param storageConnectionString string

@description('Allowed CORS origin (frontend URL). Use * only for the first bootstrap deploy.')
param corsOrigins string = '*'

@description('CPU cores for the container')
param cpu string = '1.0'

@description('Memory for the container')
param memory string = '2.0Gi'

@description('Minimum replica count')
param minReplicas int = 1

@description('Maximum replica count')
param maxReplicas int = 3

resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: useAcrRegistry ? {
    type: 'SystemAssigned, UserAssigned'
    userAssignedIdentities: {
      '${acrPullIdentityId}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8172
        transport: 'auto'
        allowInsecure: false
      }
      registries: useAcrRegistry ? [
        {
          server: acrLoginServer
          identity: acrPullIdentityId
        }
      ] : []
      secrets: [
        {
          name: 'storage-connection-string'
          value: storageConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            { name: 'PORT', value: '8172' }
            { name: 'ENVIRONMENT', value: 'production' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
            { name: 'PROJECT_ENDPOINT', value: openAiEndpoint }
            { name: 'MODEL_DEPLOYMENT_NAME', value: chatModelDeploymentName }
            { name: 'AZURE_REALTIME_ENDPOINT', value: voiceLiveEndpoint }
            { name: 'VOICE_MODEL_DEPLOYMENT', value: realtimeModelDeploymentName }
            { name: 'STORAGE_BACKEND', value: 'azure' }
            { name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'storage-connection-string' }
            { name: 'CORS_ORIGINS', value: corsOrigins }
            { name: 'WS_MAX_CONNECTIONS', value: '100' }
            { name: 'WS_CONNECTION_TIMEOUT', value: '300' }
            { name: 'LOG_LEVEL', value: 'INFO' }
          ]
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8172
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

output fqdn string = backendApp.properties.configuration.ingress.fqdn
output principalId string = backendApp.identity.principalId
output name string = backendApp.name
