@description('Name of the Azure OpenAI (Cognitive Services) account')
param name string

@description('Azure region for the OpenAI account (must support the requested models)')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Chat model name (e.g. gpt-4.1)')
param chatModelName string = 'gpt-4.1'

@description('Chat model version')
param chatModelVersion string = '2025-04-14'

@description('Chat model deployment capacity (thousands of tokens per minute, in units of 1K TPM)')
param chatModelCapacity int = 30

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: chatModelName
  sku: {
    name: 'GlobalStandard'
    capacity: chatModelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
  }
}

output accountId string = openAi.id
output accountName string = openAi.name
output endpoint string = openAi.properties.endpoint
output principalId string = openAi.identity.principalId
