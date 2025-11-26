terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "rg-marketing-agents"
  location = "East US"
}

# Azure OpenAI Service
resource "azurerm_cognitive_account" "openai" {
  name                = "openai-marketing-agents"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"
  
  identity {
    type = "SystemAssigned"
  }
}

# Cosmos DB
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-marketing-agents"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  
  consistency_policy {
    consistency_level = "Session"
  }
  
  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }
}

# Azure AI Search
resource "azurerm_search_service" "main" {
  name                = "search-marketing-agents"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"
  
  identity {
    type = "SystemAssigned"
  }
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "appi-marketing-agents"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
}

# App Configuration
resource "azurerm_app_configuration" "main" {
  name                = "appconfig-marketing-agents"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"
  
  identity {
    type = "SystemAssigned"
  }
}

# Outputs
output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "cosmos_endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "search_endpoint" {
  value = "https://${azurerm_search_service.main.name}.search.windows.net"
}