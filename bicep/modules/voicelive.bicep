@description('Name of the Azure AI Services (Foundry) account used for Voice Live')
param name string

@description('Azure region for the Voice Live account (must support the requested realtime model)')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Realtime voice model name')
param realtimeModelName string = 'gpt-realtime'

@description('Realtime voice model version')
param realtimeModelVersion string = '2025-08-28'

@description('Realtime voice model deployment capacity')
param realtimeModelCapacity int = 1

// The Azure Voice Live API (wss://<resource>.cognitiveservices.azure.com/voice-live/realtime)
// is only exposed on Azure AI Services / Microsoft Foundry accounts (kind: AIServices).
// A plain Azure OpenAI account (kind: OpenAI) does not serve this endpoint and returns
// HTTP 400 on the WebSocket upgrade.
resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
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

resource realtimeDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: realtimeModelName
  sku: {
    name: 'GlobalStandard'
    capacity: realtimeModelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: realtimeModelName
      version: realtimeModelVersion
    }
  }
}

output accountId string = aiServices.id
output accountName string = aiServices.name
output endpoint string = aiServices.properties.endpoint
output principalId string = aiServices.identity.principalId
