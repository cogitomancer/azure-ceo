# Azure Container Apps Deployment

This directory contains scripts and documentation for deploying the Marketing Agent API to Azure Container Apps.

## Prerequisites

1. **Azure CLI** installed and configured
   ```bash
   # Install Azure CLI
   # Visit: https://docs.microsoft.com/cli/azure/install-azure-cli
   
   # Login to Azure
   az login
   
   # Set your subscription (if you have multiple)
   az account set --subscription "your-subscription-id"
   ```

2. **Docker** installed and running
   ```bash
   docker --version
   ```

3. **Azure Resources** already created:
   - Azure OpenAI
   - Azure AI Search
   - Azure Cosmos DB
   - (Optional) Application Insights

## Quick Start

### 1. Configure Deployment Settings

Edit `deploy.sh` and update these variables:
```bash
RESOURCE_GROUP="rg-marketing-agents"        # Your resource group name
LOCATION="eastus"                           # Azure region
CONTAINER_APP_NAME="marketing-agent-api"    # Container app name
CONTAINER_APP_ENV="marketing-agents-env"    # Container Apps environment name
REGISTRY_NAME="acrmarketingagents"          # Azure Container Registry name (lowercase, alphanumeric)
```

### 2. Make Scripts Executable

```bash
chmod +x deployment/container-apps/deploy.sh
chmod +x deployment/container-apps/set-env.sh
```

### 3. Deploy the Container

```bash
cd /home/dev254/Public/Documents/Code/Agents/azure-ceo
./deployment/container-apps/deploy.sh
```

This script will:
- Create resource group (if it doesn't exist)
- Create Azure Container Registry (if it doesn't exist)
- Build and push Docker image to ACR
- Create Container Apps environment (if it doesn't exist)
- Create or update the Container App

### 4. Set Environment Variables

After deployment, set the required environment variables:

**Option A: Interactive Script**
```bash
./deployment/container-apps/set-env.sh
```

**Option B: Manual via Azure CLI**
```bash
az containerapp update \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --set-env-vars \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
    AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net" \
    AZURE_SEARCH_ADMIN_KEY="your-key" \
    COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com:443/" \
    COSMOS_DB_KEY="your-key" \
    COSMOS_DB_DATABASE="marketing_agents" \
    COSMOS_DB_CONTAINER="conversations" \
    COMPANY_ID="hudson_street"
```

**Option C: Via Azure Portal**
1. Go to Azure Portal → Container Apps → Your App
2. Navigate to "Environment variables"
3. Add each variable

### 5. Verify Deployment

```bash
# Get the Container App URL
az containerapp show \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --query properties.configuration.ingress.fqdn -o tsv

# Test health endpoint
curl https://your-app-url.azurecontainerapps.io/health
```

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Build and Push Docker Image

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-marketing-agents --location eastus

# Create Azure Container Registry
az acr create \
  --resource-group rg-marketing-agents \
  --name acrmarketingagents \
  --sku Basic \
  --admin-enabled true

# Login to ACR
az acr login --name acrmarketingagents

# Build and tag image
docker build -t marketing-agent-api:latest -f deployment/docker/Dockerfile .
docker tag marketing-agent-api:latest acrmarketingagents.azurecr.io/marketing-agent-api:latest

# Push to ACR
docker push acrmarketingagents.azurecr.io/marketing-agent-api:latest
```

### 2. Create Container Apps Environment

```bash
az containerapp env create \
  --name marketing-agents-env \
  --resource-group rg-marketing-agents \
  --location eastus
```

### 3. Create Container App

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name acrmarketingagents --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name acrmarketingagents --query passwords[0].value -o tsv)

# Create Container App
az containerapp create \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --environment marketing-agents-env \
  --image acrmarketingagents.azurecr.io/marketing-agent-api:latest \
  --registry-server acrmarketingagents.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
    AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net" \
    AZURE_SEARCH_ADMIN_KEY="your-key" \
    COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com:443/" \
    COSMOS_DB_KEY="your-key"
```

## Updating the Deployment

### Update Container Image

```bash
# Rebuild and push
docker build -t marketing-agent-api:latest -f deployment/docker/Dockerfile .
docker tag marketing-agent-api:latest acrmarketingagents.azurecr.io/marketing-agent-api:latest
docker push acrmarketingagents.azurecr.io/marketing-agent-api:latest

# Update Container App
az containerapp update \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --image acrmarketingagents.azurecr.io/marketing-agent-api:latest
```

### Update Environment Variables

```bash
az containerapp update \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --set-env-vars KEY=VALUE
```

### Scale the App

```bash
# Scale to 5 replicas
az containerapp update \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --min-replicas 2 \
  --max-replicas 5
```

## Monitoring and Logs

### View Logs

```bash
# Stream logs
az containerapp logs show \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --follow

# View recent logs
az containerapp logs show \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents \
  --tail 100
```

### View Metrics

```bash
# Get Container App details
az containerapp show \
  --name marketing-agent-api \
  --resource-group rg-marketing-agents
```

Or view in Azure Portal:
- Go to Container Apps → Your App → Metrics

## Troubleshooting

### Container Won't Start

1. **Check logs**:
   ```bash
   az containerapp logs show --name marketing-agent-api --resource-group rg-marketing-agents
   ```

2. **Verify environment variables**:
   ```bash
   az containerapp show --name marketing-agent-api --resource-group rg-marketing-agents --query properties.template.containers[0].env
   ```

3. **Check health endpoint**:
   ```bash
   curl https://your-app-url.azurecontainerapps.io/health
   ```

### Image Pull Errors

1. **Verify ACR credentials**:
   ```bash
   az acr credential show --name acrmarketingagents
   ```

2. **Check image exists**:
   ```bash
   az acr repository show-tags --name acrmarketingagents --repository marketing-agent-api
   ```

### Connection Issues

1. **Verify network connectivity** - Container Apps can access Azure services via managed identity or connection strings
2. **Check firewall rules** - Ensure Azure services allow connections from Container Apps
3. **Verify endpoints** - Ensure all Azure service endpoints are correct

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | Model deployment name (e.g., gpt-4o) |
| `AZURE_OPENAI_API_VERSION` | No | API version (default: 2024-02-01) |
| `AZURE_SEARCH_ENDPOINT` | Yes | Azure AI Search endpoint |
| `AZURE_SEARCH_ADMIN_KEY` | Yes | Search admin key |
| `AZURE_SEARCH_INDEX` | No | Index name (from config) |
| `COSMOS_DB_ENDPOINT` | Yes | Cosmos DB endpoint URL |
| `COSMOS_DB_KEY` | Yes | Cosmos DB access key |
| `COSMOS_DB_DATABASE` | No | Database name (default: marketing_agents) |
| `COSMOS_DB_CONTAINER` | No | Container name (default: conversations) |
| `COMPANY_ID` | No | Company identifier (default: hudson_street) |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | No | Application Insights connection string |
| `AZURE_CONTENT_SAFETY_ENDPOINT` | No | Content Safety endpoint |
| `AZURE_CONTENT_SAFETY_KEY` | No | Content Safety key |

## Cost Optimization

- **Use Consumption plan** - Pay only for what you use
- **Set min-replicas to 0** - Scale to zero when not in use (if supported)
- **Adjust CPU/Memory** - Start with 1.0 CPU and 2.0Gi memory, adjust based on usage
- **Use managed identity** - Avoid storing credentials in environment variables when possible

## Next Steps

1. ✅ Deploy Container App
2. ✅ Set environment variables
3. ✅ Test health endpoint
4. ✅ Configure custom domain (optional)
5. ✅ Set up CI/CD pipeline (see GitHub Actions workflow)
6. ✅ Configure autoscaling rules
7. ✅ Set up monitoring alerts

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Azure Container Apps Pricing](https://azure.microsoft.com/pricing/details/container-apps/)
- [Container Apps Best Practices](https://docs.microsoft.com/azure/container-apps/best-practices)

