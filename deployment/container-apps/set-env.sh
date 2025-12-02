#!/bin/bash
# Set Environment Variables for Azure Container App
# This script sets all required environment variables for the marketing agent API
# It reads from .env file if available, and only prompts for missing values

set -e

# Configuration - Update these values
RESOURCE_GROUP="azure-ceo"
CONTAINER_APP_NAME="marketing-agent-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Setting Environment Variables ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed.${NC}"
    exit 1
fi

# Get project root directory (parent of deployment/container-apps)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Load .env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}Loading environment variables from .env file...${NC}"
    # Export variables from .env file, only processing KEY=VALUE lines
    set -a
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        
        # Only process lines that look like KEY=VALUE (with optional quotes)
        if [[ "$line" =~ ^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*= ]]; then
            # Remove leading/trailing whitespace
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            # Export the variable
            export "$line" 2>/dev/null || true
        fi
    done < "$ENV_FILE"
    set +a
    echo -e "${GREEN}✓ Loaded .env file${NC}"
else
    echo -e "${YELLOW}⚠ .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Will prompt for all values...${NC}"
fi

# Function to prompt for value if not set
prompt_if_empty() {
    local var_name=$1
    local prompt_text=$2
    local default_value=$3
    local is_secret=${4:-false}
    
    if [ -z "${!var_name}" ]; then
        if [ "$is_secret" = true ]; then
            read -sp "$prompt_text: " value
            echo ""
        else
            if [ -n "$default_value" ]; then
                read -p "$prompt_text (default: $default_value): " value
                value=${value:-$default_value}
            else
                read -p "$prompt_text: " value
            fi
        fi
        eval "$var_name=\"$value\""
    else
        if [ "$is_secret" = true ]; then
            echo -e "${GREEN}✓ $prompt_text: [REDACTED]${NC}"
        else
            echo -e "${GREEN}✓ $prompt_text: ${!var_name}${NC}"
        fi
    fi
}

echo ""
echo -e "${YELLOW}Checking required environment variables...${NC}"

# Prompt for missing environment variables
prompt_if_empty "AZURE_OPENAI_ENDPOINT" "Azure OpenAI Endpoint"
prompt_if_empty "AZURE_OPENAI_DEPLOYMENT" "Azure OpenAI Deployment Name"
prompt_if_empty "AZURE_OPENAI_API_VERSION" "Azure OpenAI API Version" "2024-02-01"
prompt_if_empty "AZURE_SEARCH_ENDPOINT" "Azure AI Search Endpoint"
prompt_if_empty "AZURE_SEARCH_ADMIN_KEY" "Azure AI Search Admin Key" "" true
prompt_if_empty "COSMOS_DB_ENDPOINT" "Cosmos DB Endpoint"
prompt_if_empty "COSMOS_DB_KEY" "Cosmos DB Key" "" true
prompt_if_empty "COSMOS_DB_DATABASE" "Cosmos DB Database Name" "marketing_agents"
prompt_if_empty "COSMOS_DB_CONTAINER" "Cosmos DB Container Name" "conversations"
prompt_if_empty "COMPANY_ID" "Company ID" "hudson_street"

# Optional variables
if [ -z "$APPLICATIONINSIGHTS_CONNECTION_STRING" ]; then
    read -p "Application Insights Connection String (optional, press Enter to skip): " APPLICATIONINSIGHTS_CONNECTION_STRING
fi

# Build environment variables string
ENV_VARS="AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT"
ENV_VARS="$ENV_VARS AZURE_OPENAI_DEPLOYMENT=$AZURE_OPENAI_DEPLOYMENT"
ENV_VARS="$ENV_VARS AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION"
ENV_VARS="$ENV_VARS AZURE_SEARCH_ENDPOINT=$AZURE_SEARCH_ENDPOINT"
ENV_VARS="$ENV_VARS AZURE_SEARCH_ADMIN_KEY=$AZURE_SEARCH_ADMIN_KEY"
ENV_VARS="$ENV_VARS COSMOS_DB_ENDPOINT=$COSMOS_DB_ENDPOINT"
ENV_VARS="$ENV_VARS COSMOS_DB_KEY=$COSMOS_DB_KEY"
ENV_VARS="$ENV_VARS COSMOS_DB_DATABASE=$COSMOS_DB_DATABASE"
ENV_VARS="$ENV_VARS COSMOS_DB_CONTAINER=$COSMOS_DB_CONTAINER"
ENV_VARS="$ENV_VARS COMPANY_ID=$COMPANY_ID"

if [ -n "$APPLICATIONINSIGHTS_CONNECTION_STRING" ]; then
    ENV_VARS="$ENV_VARS APPLICATIONINSIGHTS_CONNECTION_STRING=$APPLICATIONINSIGHTS_CONNECTION_STRING"
fi

# Update Container App with environment variables
echo -e "${YELLOW}Updating Container App environment variables...${NC}"
az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars $ENV_VARS \
    --output none

echo -e "${GREEN}=== Environment Variables Set Successfully! ===${NC}"
echo -e "${YELLOW}The Container App will restart with the new environment variables.${NC}"

