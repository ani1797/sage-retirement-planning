@description('Name of the Container Apps environment')
param name string

@description('Azure region for the environment')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Log Analytics customer ID')
param logAnalyticsCustomerId string

@secure()
@description('Log Analytics shared key')
param logAnalyticsSharedKey string

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

output environmentId string = environment.id
output environmentName string = environment.name
output defaultDomain string = environment.properties.defaultDomain
