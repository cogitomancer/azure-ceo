# Azure Setup Guide

Step-by-step setup for Azure services required by the Multi-Agent Marketing System.

The system supports multiple companies with separate Azure resources. **Hudson Street Bakery** is the default company.

---

## Overview

### Required Services

| Service | Purpose |
|---------|---------|
| Azure OpenAI | LLM for agents (gpt-4o, gpt-4-turbo) |
| Azure AI Search | RAG for products/brand rules |
| Azure Cosmos DB | Campaign state storage |
| Azure SQL Database | Customer segmentation data |
| Application Insights | Monitoring and logging |
| Azure Content Safety | Content validation |

### Company-Specific Resources

Each company uses separate Azure resources:

| Resource | Hudson Street Bakery | Microsoft |
|----------|---------------------|-----------|
| AI Search Index | `hudson-street-products` | `microsoft-azure-products` |
| Semantic Config | `hudson-street-semantic` | `microsoft-semantic` |
| SQL Database | `hudson_street_marketing` | `microsoft_marketing` |
| Cosmos Container | `hudson_street_campaigns` | `microsoft_campaigns` |

---

## 1. Azure OpenAI (Required)

**Purpose**: LLM provider for the 5 marketing agents

### Setup

1. Portal → **Create a resource** → **"Azure OpenAI"**
2. **Basics**:
   - Resource group: `marketing-agents-rg` (create new)
   - Region: East US (or your region)
   - Name: `marketing-agents-openai`
   - Pricing tier: **S0**
3. **Review + Create** → **Create**

### Deploy Models

1. Go to Azure AI Foundry: https://ai.azure.com/
2. Select your Azure OpenAI resource
3. **Deployments** → **Create new deployment**
4. Deploy these models:
   - Model: `gpt-4o` → Deployment name: `gpt-4o`
   - Model: `gpt-4-turbo` → Deployment name: `gpt-4-turbo`

### Get Endpoint

1. Azure Portal → Your OpenAI resource → **Keys and Endpoint**
2. Copy **Endpoint** (e.g., `https://marketing-agents-openai.openai.azure.com/`)

### Add to `.env`

```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

---

## 2. Azure AI Search (Required)

**Purpose**: RAG for grounded product information and brand rules

### Setup

1. Portal → **Create a resource** → **"Azure AI Search"**
2. **Basics**:
   - Resource group: `marketing-agents-rg`
   - Service name: `marketing-agents-search`
   - Location: Same as OpenAI
   - Pricing tier: **Basic** (or Free for testing)
3. **Review + Create** → **Create**

### Create Company Index

Create an index for each company. For Hudson Street Bakery:

1. **Indexes** → **+ Add index** → **JSON** tab
2. Paste this schema:

```json
{
  "name": "hudson-street-products",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "product_name", "type": "Edm.String", "searchable": true},
    {"name": "category", "type": "Edm.String", "filterable": true},
    {"name": "source_file", "type": "Edm.String", "filterable": true},
    {"name": "page_number", "type": "Edm.Int32", "filterable": true}
  ],
  "semantic": {
    "configurations": [{
      "name": "hudson-street-semantic",
      "prioritizedFields": {
        "titleField": {"fieldName": "title"},
        "prioritizedContentFields": [{"fieldName": "content"}]
      }
    }]
  }
}
```

3. **Create**

### Upload Company Data

Index data from the `tables/` folder:

1. **Search explorer** → Select index: `hudson-street-products`
2. **Upload documents** → Upload data from:
   - `tables/Hudson_street/products.json`
   - `tables/Hudson_street/brand_rules.json`

For Microsoft, create index `microsoft-azure-products` with semantic config `microsoft-semantic`.

### Get Endpoint & Key

1. **Overview** → Copy **URL**
2. **Keys** → Copy **Primary admin key**

### Add to `.env`

```bash
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key
AZURE_SEARCH_INDEX=product-docs
```

> **Note**: The index name in `.env` is a default. The system automatically selects the company-specific index based on `COMPANY_ID`.

---

## 3. Azure Cosmos DB (Required)

**Purpose**: Campaign state and conversation persistence

### Setup

1. Portal → **Create a resource** → **"Azure Cosmos DB"**
2. Select **Azure Cosmos DB for NoSQL**
3. **Basics**:
   - Resource group: `marketing-agents-rg`
   - Account name: `marketing-agents-cosmos`
   - Location: Same as other resources
   - Capacity mode: **Serverless** (for testing)
4. **Review + Create** → **Create**

### Create Database & Containers

1. Go to Cosmos DB → **Data Explorer**
2. **New Database**: `marketing_agents`
3. **New Container** for each company:
   - Container: `hudson_street_campaigns`
   - Partition key: `/sessionId`
4. Repeat for Microsoft: `microsoft_campaigns`

### Get Endpoint & Key

1. **Keys** → Copy **URI** and **Primary Key**

### Add to `.env`

```bash
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key
COSMOS_DB_DATABASE=marketing_agents
COSMOS_DB_CONTAINER=conversations
```

> **Note**: The container in `.env` is a default. The system automatically selects the company-specific container based on `COMPANY_ID`.

---

## 4. Azure SQL Database (Required)

**Purpose**: Customer segmentation data

### Setup

1. Portal → **Create a resource** → **"Azure SQL Database"**
2. **Basics**:
   - Resource group: `marketing-agents-rg`
   - Database name: `marketing_customers`
   - Server: Create new → pick your region
   - Compute: **Serverless** (auto-pause saves costs)
3. **Networking**: Allow Azure services access
4. **Review + Create** → **Create**

### Create Customer Table

Connect via Azure Portal Query Editor or Azure Data Studio:

```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    segment VARCHAR(50),
    total_purchases INT,
    lifetime_value DECIMAL(10,2),
    last_purchase_date DATE,
    is_active BIT DEFAULT 1
);
```

### Load Customer Data

Import CSV data from `tables/` folder:
- `tables/Hudson_street/customers.csv`
- `tables/Microsoft/Global Customer Segmentation Mock Data.csv`

Use Azure Portal → Query Editor → Import or Azure Data Studio.

### Get Connection String

1. Azure Portal → SQL Database → **Connection strings**
2. Copy the **ADO.NET** connection string

### Add to `.env`

```bash
AZURE_SQL_CONNECTION_STRING=Server=tcp:your-server.database.windows.net,1433;Database=marketing_customers;User ID=your-user;Password=your-password;Encrypt=true;
```

---

## 5. Application Insights (Required)

**Purpose**: Monitoring and logging

### Setup

1. Portal → **Create a resource** → **"Application Insights"**
2. **Basics**:
   - Resource group: `marketing-agents-rg`
   - Name: `marketing-agents-insights`
3. **Review + Create** → **Create**

### Get Connection String

1. **Overview** → Copy **Connection String**

### Add to `.env`

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

---

## 6. Azure Content Safety (Required)

**Purpose**: Content validation and compliance filtering

### Setup

1. Portal → **Create a resource** → **"Content Safety"**
2. **Basics**:
   - Resource group: `marketing-agents-rg`
   - Name: `marketing-agents-safety`
   - Region: Same as other resources
   - Pricing tier: **S0**
3. **Review + Create** → **Create**

### Get Endpoint & Key

1. **Keys and Endpoint** → Copy **Endpoint** and **Key 1**

### Add to `.env`

```bash
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key
```

---

## Complete `.env` Configuration

```bash
# Azure OpenAI (Required)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure AI Search (Required)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key
AZURE_SEARCH_INDEX=product-docs

# Azure Cosmos DB (Required)
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key
COSMOS_DB_DATABASE=marketing_agents
COSMOS_DB_CONTAINER=conversations

# Application Insights (Required)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Azure SQL Database (Required)
AZURE_SQL_CONNECTION_STRING=Server=tcp:your-server.database.windows.net,1433;Database=marketing_customers;User ID=your-user;Password=your-password;Encrypt=true;

# Azure Content Safety (Required)
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key

# Company Selection (default: hudson_street)
COMPANY_ID=hudson_street
```

---

## Authentication

### Option A: Azure CLI (Development)

```bash
az login
az account show
```

The system uses `DefaultAzureCredential` which picks up your Azure CLI credentials.

### Option B: Service Principal (Production)

Create a service principal with appropriate RBAC roles for each Azure service.

---

## Verify Setup

### 1. Start Backend

```bash
uvicorn api.main:app --reload --port 8000
```

### 2. Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "marketing-agent-api",
  "version": "1.0.0",
  "company": "Hudson Street Bakery",
  "company_id": "hudson_street"
}
```

### 3. Check Company Endpoint

```bash
curl http://localhost:8000/company
```

Shows company info and which Azure resources are being used.

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and create a test campaign.

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Azure Search error" | Verify `AZURE_SEARCH_ENDPOINT` and `AZURE_SEARCH_ADMIN_KEY`. Ensure index exists. |
| "Could not load company data" | Check `tables/` folder exists. Verify `COMPANY_ID` is valid. |
| "Authentication failed" | Run `az login` or check service principal credentials. |
| "Cosmos DB connection failed" | Verify endpoint and key. Ensure database and container exist. |

---

## Switching Companies

Set `COMPANY_ID` in `.env` to switch between companies:

```bash
# Default: Hudson Street Bakery
COMPANY_ID=hudson_street

# Switch to Microsoft
COMPANY_ID=microsoft
```

The system automatically uses the correct Azure resources for each company.

---

## Cost Estimates

| Service | Pricing Tier | Estimated Cost |
|---------|--------------|----------------|
| Azure OpenAI | S0 | $100-500/month |
| Azure AI Search | Basic | $75/month |
| Cosmos DB | Serverless | $25-100/month |
| Application Insights | Pay-as-you-go | $10-50/month |
| Azure SQL Database | Serverless | $5-50/month |
| Azure Content Safety | S0 | $50-100/month |

---

## Data Indexing Reference

The `tables/` folder contains reference data to index into Azure:

```
tables/
├── Hudson_street/
│   ├── brand_rules.json    → Index into hudson-street-products
│   ├── products.json       → Index into hudson-street-products  
│   └── customers.csv       → Load into Synapse hudson_street_marketing
│
└── Microsoft/
    ├── Dataset 1_...txt    → Index into microsoft-azure-products
    ├── Dataset 2_...txt    → Index into microsoft-azure-products
    └── Dataset 3_...csv    → Load into Synapse microsoft_marketing
```

Use the Azure AI Search data import wizard or SDK to index the JSON files.
