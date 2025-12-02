#!/bin/bash
# Azure Container Apps Deployment Script
# This script deploys the marketing agent API to Azure Container Apps

set -e

# Configuration - Update these values
RESOURCE_GROUP="azure-ceo"
LOCATION="eastus"
CONTAINER_APP_NAME="marketing-agent-api"
CONTAINER_APP_ENV="marketing-agents-env"
REGISTRY_NAME="acrmarketingagents"  # Azure Container Registry name (lowercase, alphanumeric only)
IMAGE_NAME="marketing-agent-api"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Azure Container Apps Deployment ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo -e "${YELLOW}Checking Azure login status...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in. Please log in to Azure...${NC}"
    az login
fi

# Get subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}Using subscription: ${SUBSCRIPTION_ID}${NC}"

# Register required resource providers
echo -e "${YELLOW}Registering required Azure resource providers...${NC}"
az provider register --namespace Microsoft.ContainerRegistry --wait --output none || true
az provider register --namespace Microsoft.App --wait --output none || true
az provider register --namespace Microsoft.OperationalInsights --wait --output none || true
echo -e "${GREEN}Resource providers registered${NC}"

# Create resource group if it doesn't exist
echo -e "${YELLOW}Creating resource group if it doesn't exist...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# Create Azure Container Registry if it doesn't exist
echo -e "${YELLOW}Creating Azure Container Registry if it doesn't exist...${NC}"
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}Creating ACR: ${REGISTRY_NAME}${NC}"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none
else
    echo -e "${GREEN}ACR already exists${NC}"
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
echo -e "${GREEN}ACR Login Server: ${ACR_LOGIN_SERVER}${NC}"

# Build and push Docker image
cd "$(dirname "$0")/../.."

# Check if Docker is available, if not use ACR build
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo -e "${YELLOW}Building Docker image locally...${NC}"
    docker build -t $IMAGE_NAME:$IMAGE_TAG -f deployment/docker/Dockerfile .
    
    echo -e "${YELLOW}Tagging image for ACR...${NC}"
    docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
    
    echo -e "${YELLOW}Logging into ACR...${NC}"
    az acr login --name $REGISTRY_NAME
    
    echo -e "${YELLOW}Pushing image to ACR...${NC}"
    docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
else
    echo -e "${YELLOW}Docker not available, using Azure Container Registry build service...${NC}"
    echo -e "${YELLOW}Building and pushing image using ACR Tasks...${NC}"
    az acr build \
        --registry $REGISTRY_NAME \
        --image $IMAGE_NAME:$IMAGE_TAG \
        --file deployment/docker/Dockerfile \
        .
fi

# Create Container Apps environment if it doesn't exist
echo -e "${YELLOW}Creating Container Apps environment if it doesn't exist...${NC}"
if ! az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}Creating Container Apps environment...${NC}"
    az containerapp env create \
        --name $CONTAINER_APP_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
else
    echo -e "${GREEN}Container Apps environment already exists${NC}"
fi

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)

# Create or update Container App
echo -e "${YELLOW}Creating/updating Container App...${NC}"
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}Updating existing Container App...${NC}"
    
    # Configure registry if not already configured
    echo -e "${YELLOW}Configuring registry credentials...${NC}"
    # Check if registry is already configured
    if ! az containerapp registry list --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "[?server=='$ACR_LOGIN_SERVER']" -o tsv | grep -q "$ACR_LOGIN_SERVER"; then
        az containerapp registry set \
            --name $CONTAINER_APP_NAME \
            --resource-group $RESOURCE_GROUP \
            --server $ACR_LOGIN_SERVER \
            --username $ACR_USERNAME \
            --password $ACR_PASSWORD \
            --output none
        echo -e "${GREEN}Registry configured${NC}"
    else
        echo -e "${GREEN}Registry already configured${NC}"
    fi
    
    # Update the container app with new image
    echo -e "${YELLOW}Updating container image...${NC}"
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
        --output none
else
    echo -e "${YELLOW}Creating new Container App...${NC}"
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port 8000 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 1.0 \
        --memory 2.0Gi \
        --output none
fi

# Get the Container App URL
APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Container App URL: https://${APP_URL}${NC}"
echo -e "${GREEN}Health Check: https://${APP_URL}/health${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set environment variables using: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --set-env-vars KEY=VALUE"
echo "2. Or use the set-env.sh script to set all required environment variables"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"

