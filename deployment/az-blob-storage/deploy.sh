#!/bin/bash
# Deploy Frontend to Azure Blob Storage Static Website
# This works in any Azure region including eastus

set -e

# Configuration
RESOURCE_GROUP="azure-ceo"
STORAGE_ACCOUNT_NAME="azureceo"  # Using existing storage account
LOCATION="eastus"
CONTAINER_NAME="\$web"  # Static website container name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Deploying Frontend to Azure Blob Storage ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in. Please log in to Azure...${NC}"
    az login
fi

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

# Build frontend for production (uses .env.production)
echo -e "${YELLOW}Building frontend for production...${NC}"
cd "$FRONTEND_DIR"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production file not found!${NC}"
    echo -e "${YELLOW}Create .env.production with: VITE_API_URL=https://marketing-agent-api.delightfulbeach-185bfb37.eastus.azurecontainerapps.io${NC}"
    exit 1
fi

# Build for production mode (uses .env.production)
npm run build -- --mode production

if [ ! -d "dist" ]; then
    echo -e "${RED}Error: Build failed or dist directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend built for production${NC}"

# Register resource provider if needed
echo -e "${YELLOW}Registering required resource providers...${NC}"
az provider register --namespace Microsoft.Storage --wait --output none || true

# Create storage account if it doesn't exist
echo -e "${YELLOW}Creating storage account if it doesn't exist...${NC}"
if ! az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}Creating storage account: ${STORAGE_ACCOUNT_NAME}${NC}"
    az storage account create \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --output none
    
    echo -e "${GREEN}✓ Storage account created${NC}"
else
    echo -e "${GREEN}✓ Storage account already exists${NC}"
fi

# Enable static website hosting
echo -e "${YELLOW}Enabling static website hosting...${NC}"
az storage blob service-properties update \
    --account-name $STORAGE_ACCOUNT_NAME \
    --static-website \
    --404-document index.html \
    --index-document index.html \
    --output none

# Get storage account key
echo -e "${YELLOW}Getting storage account key...${NC}"
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT_NAME \
    --query "[0].value" -o tsv)

# Upload files to blob storage
echo -e "${YELLOW}Uploading frontend files...${NC}"
cd "$DIST_DIR"

# Upload all files with proper content types
az storage blob upload-batch \
    --account-name $STORAGE_ACCOUNT_NAME \
    --account-key "$STORAGE_KEY" \
    --destination "\$web" \
    --source "." \
    --overwrite \
    --output none

# Get the static website URL
PRIMARY_ENDPOINT=$(az storage account show \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "primaryEndpoints.web" -o tsv)

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Frontend URL: ${PRIMARY_ENDPOINT}${NC}"
echo -e "${GREEN}Backend API: https://marketing-agent-api.delightfulbeach-185bfb37.eastus.azurecontainerapps.io${NC}"
echo ""
echo -e "${YELLOW}Important: The frontend was built with production mode using .env.production${NC}"
echo -e "${YELLOW}Backend API URL: https://marketing-agent-api.delightfulbeach-185bfb37.eastus.azurecontainerapps.io${NC}"
echo ""
echo -e "${BLUE}To update the deployment, just run this script again${NC}"
echo -e "${BLUE}It will rebuild with production settings automatically${NC}"

