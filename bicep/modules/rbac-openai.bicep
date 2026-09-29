@description('Principal ID of the backend Container App system-assigned identity')
param backendPrincipalId string

@description('Resource ID of the Azure OpenAI account')
param openAiId string

var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User

resource openAiRef 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(openAiId, '/'))
}

resource backendOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiId, backendPrincipalId, openAiUserRoleId)
  scope: openAiRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}
