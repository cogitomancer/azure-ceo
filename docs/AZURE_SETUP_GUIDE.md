# Complete Azure Setup Guide

Step-by-step setup for all Azure services required by the Marketing Agent System. All instructions use Azure Portal only.

## Required Services

1. Azure OpenAI (Semantic Kernel)
2. Cosmos DB (State Management)
3. Azure App Configuration (Feature Flags)
4. Application Insights (Monitoring)
5. Azure Synapse Analytics (Customer Data)
6. Azure AI Search (RAG)
7. Azure AI Content Safety (Content Validation)

---

## 1. Azure OpenAI

**Purpose**: LLM provider for Semantic Kernel agents

### Setup
1. Portal → **Create a resource** → **"Azure OpenAI"**
2. **Basics**:
   - Resource group: Create or select
   - Region: Select region
   - Name: `your-openai` (unique)
   - Pricing tier: **S0**
3. **Review + Create** → **Create**

### Deploy Model
1. Go to your OpenAI resource → **Model deployments**
2. **+ Create** → Select **gpt-4o** or **gpt-4-turbo**
3. Deployment name: `gpt-4o`
4. **Create**

### Get Endpoint & Key
1. **Keys and Endpoint** → Copy **Endpoint** and **Key 1**
2. Add to `.env`:
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_KEY=your-key-here
```

**Cost**: ~$100-500/month (usage-based)

---

## 2. Cosmos DB

**Purpose**: State management and conversation persistence

### Setup
1. Portal → **Create a resource** → **"Azure Cosmos DB"**
2. **Basics**:
   - API: **Core (SQL)**
   - Resource group: Same as above
   - Account name: `your-cosmos` (unique)
   - Location: Same region
   - Capacity mode: **Serverless**
3. **Review + Create** → **Create**

### Create Database & Container
1. Go to Cosmos DB → **Data Explorer**
2. **New Container**:
   - Database: **New** → Name: `marketing_agents`
   - Container: `conversations`
   - Partition key: `/sessionId`
   - Throughput: **400** (or Serverless)
3. **OK**

### Get Endpoint & Key
1. **Keys** → Copy **URI** and **Primary Key**
2. Add to `.env`:
```bash
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-key-here
COSMOS_DB_DATABASE=marketing_agents
COSMOS_DB_CONTAINER=conversations
```

**Cost**: ~$25-100/month (serverless)

---

## 3. Azure App Configuration

**Purpose**: Feature flags for A/B tests

### Setup
1. Portal → **Create a resource** → **"App Configuration"**
2. **Basics**:
   - Resource group: Same
   - Name: `your-appconfig` (unique)
   - Location: Same region
   - Pricing tier: **Free** (or Standard)
3. **Review + Create** → **Create**

### Get Endpoint & Key
1. **Overview** → Copy **Endpoint URL**
2. **Access keys** → Copy **Primary key**
3. Add to `.env`:
```bash
AZURE_APP_CONFIG_ENDPOINT=https://your-appconfig.azconfig.io
```

**Cost**: Free tier available

---

## 4. Application Insights

**Purpose**: Monitoring and observability

### Setup
1. Portal → **Create a resource** → **"Application Insights"**
2. **Basics**:
   - Resource group: Same
   - Name: `your-insights` (unique)
   - Region: Same region
   - Application type: **Web**
3. **Review + Create** → **Create**

### Get Connection String
1. **Overview** → Copy **Connection String**
2. Add to `.env`:
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

**Cost**: ~$10-50/month (pay-as-you-go)

---

## 5. Azure Synapse Analytics

**Purpose**: Customer data warehouse for segmentation

### Setup
1. Portal → **Create a resource** → **"Azure Synapse Analytics"**
2. **Basics**:
   - Resource group: Same
   - Workspace name: `your-synapse` (unique)
   - Region: Same region
   - Data Lake Storage Gen2: Create new or select existing
   - SQL admin: `sqladminuser` + password
3. **Networking**: Public endpoint (for dev)
4. **Review + Create** → **Create**

### Create SQL Pool
1. Synapse workspace → **SQL pools** → **+ New**
2. Name: `marketing_dwh`
3. Performance level: **DW100c**
4. **Create**

### Create Schema
1. **Develop** → **+** → **SQL script**
2. Connect to: `marketing_dwh`
3. Run:
```sql
CREATE SCHEMA customer_data;
GO

CREATE TABLE customer_data.customers_active_runners (
    customer_id BIGINT PRIMARY KEY,
    email_hash VARCHAR(64),
    total_purchases INT,
    lifetime_value DECIMAL(10,2),
    is_active BIT DEFAULT 1
)
WITH (DISTRIBUTION = HASH(customer_id), CLUSTERED COLUMNSTORE INDEX);
GO
```

### Get Endpoint
1. **Overview** → Copy **Workspace web URL**
2. Add to `.env`:
```bash
AZURE_SYNAPSE_ENDPOINT=https://your-synapse.dev.azuresynapse.net
AZURE_SYNAPSE_DATABASE=marketing_dwh
```

**Important**: Pause SQL pool when not in use to save costs (SQL pools → marketing_dwh → Pause)

**Cost**: ~$500-2,000/month (pause pool when not in use)

---

## 6. Azure AI Search

**Purpose**: RAG for grounded content generation

### Setup
1. Portal → **Create a resource** → **"Azure AI Search"**
2. **Basics**:
   - Resource group: Same
   - Service name: `your-search` (unique)
   - Location: Same region
   - Pricing tier: **Standard** (required for semantic)
3. **Review + Create** → **Create**

### Create Index
1. **Indexes** → **+ Add index**
2. **JSON** tab → Paste:
```json
{
  "name": "product-docs",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "source_file", "type": "Edm.String", "filterable": true},
    {"name": "page_number", "type": "Edm.Int32", "filterable": true}
  ],
  "semantic": {
    "configurations": [{
      "name": "default",
      "prioritizedFields": {
        "titleField": {"fieldName": "title"},
        "prioritizedContentFields": [{"fieldName": "content"}]
      }
    }]
  }
}
```
3. **Create**

### Upload Documents
1. **Search explorer** → Select index: `product-docs`
2. **Upload documents** → Paste JSON:
```json
{
  "value": [{
    "id": "doc001",
    "content": "Product features and specifications...",
    "title": "Product Specs",
    "source_file": "specs.pdf",
    "page_number": 1
  }]
}
```
3. **Upload**

### Get Endpoint & Key
1. **Overview** → Copy **URL**
2. **Keys** → Copy **Primary admin key**
3. Add to `.env`:
```bash
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX=product-docs
AZURE_SEARCH_ADMIN_KEY=your-key-here
```

**Cost**: ~$250/month (Standard tier)

---

## 7. Azure AI Content Safety

**Purpose**: Content validation and compliance

### Setup
1. Portal → **Create a resource** → **"Content Safety"**
2. **Basics**:
   - Resource group: Same
   - Name: `your-safety` (unique)
   - Region: Same region
   - Pricing tier: **S0**
3. **Review + Create** → **Create**

### Get Endpoint & Key
1. **Keys and Endpoint** → Copy **Endpoint** and **Key 1**
2. Add to `.env`:
```bash
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key-here
```

**Cost**: ~$1 per 1,000 text records

---

## Complete Configuration

After setting up all services, create `.env` file in project root with all values:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_KEY=your-key

# Cosmos DB
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-key
COSMOS_DB_DATABASE=marketing_agents
COSMOS_DB_CONTAINER=conversations

# App Configuration
AZURE_APP_CONFIG_ENDPOINT=https://your-appconfig.azconfig.io

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Synapse
AZURE_SYNAPSE_ENDPOINT=https://your-synapse.dev.azuresynapse.net
AZURE_SYNAPSE_DATABASE=marketing_dwh

# AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX=product-docs
AZURE_SEARCH_ADMIN_KEY=your-key

# Content Safety
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key
```

---

## Testing

```bash
# Test all services
pytest tests/integration/test_complete_system.py -v -s

# Test specific services
pytest tests/integration/test_kernel_factory_integration.py -v -s
```

---

## Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Azure OpenAI | $100-500 |
| Cosmos DB | $25-100 |
| App Configuration | Free |
| Application Insights | $10-50 |
| Synapse Analytics | $500-2,000 |
| AI Search | $250 |
| Content Safety | ~$50-100 |
| **Total** | **~$935-3,000/month** |

---

## Important Notes

- **Semantic Kernel**: Uses Azure OpenAI automatically - no separate setup needed
- **API Keys**: Copy keys immediately after creating resources (they're only shown once)
- **Pause Synapse SQL Pool**: Always pause when not in use (SQL pools → marketing_dwh → Pause)
- **Managed Identity**: Use in production instead of keys for better security
- **Region**: Keep all services in the same region for best performance
- **Testing**: After setup, run tests (see [TESTING_GUIDE.md](TESTING_GUIDE.md))
