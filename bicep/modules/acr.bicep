@description('Name of the Container Registry')
param name string

@description('Azure region for the registry')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('SKU for the registry')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output loginServer string = acr.properties.loginServer
output registryId string = acr.id
output registryName string = acr.name
