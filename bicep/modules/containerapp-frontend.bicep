@description('Name of the frontend Container App')
param name string

@description('Azure region')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Container Apps environment resource ID')
param environmentId string

@description('Full container image reference, e.g. myacr.azurecr.io/sage-frontend:tag')
param image string

@description('ACR login server (used to configure the registry on the app)')
param acrLoginServer string

@description('Whether to configure ACR pull credentials (skip for public placeholder images so the app does not wait on RBAC propagation)')
param useAcrRegistry bool = false

@description('Resource ID of the user-assigned managed identity used for ACR pull (must already have AcrPull granted)')
param acrPullIdentityId string = ''

@description('CPU cores for the container')
param cpu string = '0.5'

@description('Memory for the container')
param memory string = '1.0Gi'

@description('Minimum replica count')
param minReplicas int = 1

@description('Maximum replica count')
param maxReplicas int = 3

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
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
        targetPort: 3847
        transport: 'auto'
        allowInsecure: false
      }
      registries: useAcrRegistry ? [
        {
          server: acrLoginServer
          identity: acrPullIdentityId
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            { name: 'PORT', value: '3847' }
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

output fqdn string = frontendApp.properties.configuration.ingress.fqdn
output principalId string = frontendApp.identity.principalId
output name string = frontendApp.name
