@description('Principal ID of the backend Container App system-assigned identity')
param backendPrincipalId string

@description('Resource ID of the Azure AI Services (Foundry) account used for Voice Live')
param voiceLiveId string

// Voice Live keyless (Entra ID) auth requires both roles on the Foundry resource:
// https://learn.microsoft.com/azure/ai-services/speech-service/voice-live-how-to
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User (formerly Azure AI User)

resource voiceLiveRef 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(voiceLiveId, '/'))
}

resource backendCognitiveServicesUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(voiceLiveId, backendPrincipalId, cognitiveServicesUserRoleId)
  scope: voiceLiveRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
    principalId: backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource backendFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(voiceLiveId, backendPrincipalId, foundryUserRoleId)
  scope: voiceLiveRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
    principalId: backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}
