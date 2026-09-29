@description('Name of the Log Analytics workspace')
param name string

@description('Azure region for the workspace')
param location string

@description('Tags to apply to the resource')
param tags object = {}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

output workspaceId string = logAnalytics.id
output customerId string = logAnalytics.properties.customerId
@secure()
output sharedKey string = logAnalytics.listKeys().primarySharedKey
