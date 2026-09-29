@description('Name of the user-assigned managed identity')
param name string

@description('Azure region')
param location string

@description('Tags to apply to the resource')
param tags object = {}

resource uai 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

output identityId string = uai.id
output principalId string = uai.properties.principalId
output clientId string = uai.properties.clientId
