# Scalable Multi-Agent Marketing Personalization System

A multi-agent architecture for scalable(SMB to Enterprise level) marketing automation using Azure AI services, Semantic Kernel, and specialized AI agents to deliver compliant, data-driven marketing campaigns.

## Quick Start

### 1. Setup Azure Services
Follow **[docs/AZURE_SETUP_GUIDE.md](docs/AZURE_SETUP_GUIDE.md)** to configure required Azure services.

### 2. Install & Configure
```bash
# Clone and setup
git clone <repository-url>
cd azure-ceo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure endpoints
```

### 3. Start Backend
```bash
uvicorn api.main:app --reload --port 8000
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Company Configuration

The system supports multiple company data sets. **Hudson Street Bakery** is the default.

### Available Companies

| Company | Description | Industry |
|---------|-------------|----------|
| **Hudson Street Bakery** (default) | NYC neighborhood bakery | Food & Beverage |
| **Microsoft Azure** | Enterprise cloud services | Technology |

### Switching Companies

Set the `COMPANY_ID` environment variable:

```bash
# Default: Hudson Street Bakery
COMPANY_ID=hudson_street

# Switch to Microsoft
COMPANY_ID=microsoft
```

### Company Data Structure

Each company has data in the `tables/` directory:
- `brand_rules.json` - Brand voice, compliance rules, banned phrases
- `products.json` - Product catalog with pricing and details
- `customers.csv` - Customer segment data

This data is indexed into Azure services for production use.

---

## Architecture

### Agent Workflow

The system uses 5 specialized agents that execute sequentially:

```
┌─────────────────┐    ┌────────────────┐    ┌─────────────────┐
│  Strategy Lead  │ -> │ Data Segmenter │ -> │ Content Creator │
│  (Planning)     │    │ (Segmentation) │    │ (Copy Writing)  │
└─────────────────┘    └────────────────┘    └─────────────────┘
                                                      │
                                                      v
┌─────────────────────┐    ┌────────────────────┐
│  Experiment Runner  │ <- │ Compliance Officer │
│  (A/B Testing)      │    │ (Safety Review)    │
└─────────────────────┘    └────────────────────┘
```

### Agent Details

| Agent | Role | Model | Azure Services |
|-------|------|-------|----------------|
| **Strategy Lead** | Decomposes objectives, coordinates team | gpt-4o | Azure AI Search (RAG) |
| **Data Segmenter** | Identifies target audience segments | gpt-4-turbo | Azure SQL Database |
| **Content Creator** | Generates marketing copy with citations | gpt-4o | Azure AI Search (RAG) |
| **Compliance Officer** | Validates safety and brand compliance | gpt-4-turbo | Content Safety, Brand Rules |
| **Experiment Runner** | Configures A/B/n tests | gpt-4-turbo | Statistical Analysis |

### Azure Services per Company

| Service | Hudson Street Bakery | Microsoft |
|---------|---------------------|-----------|
| **AI Search Index** | `hudson-street-products` | `microsoft-azure-products` |
| **SQL Database** | `hudson_street_marketing` | `microsoft_marketing` |
| **Cosmos Container** | `hudson_street_campaigns` | `microsoft_campaigns` |

---

## API Endpoints

### Health & Company
- `GET /health` - Health check with active company info
- `GET /company` - Current company info and Azure resources
- `GET /company/products` - Product catalog
- `GET /company/products/search?q=<query>` - Search products
- `GET /company/brand-rules` - Brand rules and guidelines
- `GET /company/customers` - Customer segment summary

### Campaigns
- `POST /campaigns` - Create campaign (blocking)
- `POST /campaigns/stream` - Create campaign with real-time streaming (SSE)
- `GET /campaigns` - List campaigns
- `GET /campaigns/:id` - Get campaign details

### Validation
- `POST /content/validate` - Validate content safety
- `POST /segments` - Create customer segment
- `GET /experiments/:id/analysis` - Get experiment analysis

---

## Configuration Files

### `config/base_config.yaml`
Main configuration for Azure services and agent settings:

```yaml
azure_openai:
  endpoint: ${AZURE_OPENAI_ENDPOINT}
  deployment_name: gpt-4o
  api_version: "2024-02-01"

azure_search:
  endpoint: ${AZURE_SEARCH_ENDPOINT}
  index_name: product-docs  # Overridden per company

cosmos_db:
  endpoint: ${COSMOS_DB_ENDPOINT}
  database_name: marketing_agents
  container_name: conversations  # Overridden per company

agents:
  StrategyLead:
    model: gpt-4o
    temperature: 0.7
  DataSegmenter:
    model: gpt-4-turbo
    temperature: 0.3
  # ... etc
```

### `config/brand_guidelines.yaml`
Default brand compliance rules (company-specific rules loaded from tables).

### `config/safety_policies.yaml`
Content safety thresholds for Azure AI Content Safety.

---

## Project Structure

```
azure-ceo/
├── api/
│   └── main.py              # FastAPI endpoints
├── agents/
│   ├── strategy_lead.py     # Strategy agent
│   ├── data_segmenter.py    # Segmentation agent
│   ├── content_creator.py   # Content generation agent
│   ├── compliance_officer.py # Compliance agent
│   └── experiment_runner.py # Experimentation agent
├── config/
│   ├── azure_config.py      # Config loader
│   └── base_config.yaml     # Base configuration
├── core/
│   ├── orchestrator.py      # Agent orchestration
│   └── kernel_factory.py    # Semantic Kernel setup
├── frontend/
│   └── src/                 # React frontend
├── plugins/
│   ├── content/
│   │   └── rag_plugin.py    # Azure AI Search RAG
│   ├── data/
│   │   └── cdp_plugin.py    # Azure SQL Database queries
│   └── safety/
│       └── brand_compliance_plugin.py
├── services/
│   ├── company_data_service.py  # Company configuration
│   ├── cosmos_service.py        # Cosmos DB client
│   └── monitor_service.py       # Application Insights
├── tables/
│   ├── Hudson_street/       # Hudson Street Bakery data
│   └── Microsoft/           # Microsoft Azure data
└── workflows/
    └── campaign_creation.py # Campaign workflow
```

---

## Frontend Features

- **Real-time workflow progress** - Visual indicator showing current agent stage
- **Company info display** - Shows active company and product count
- **Agent collaboration view** - Color-coded messages from each agent
- **Streaming updates** - Live updates via Server-Sent Events

---

## Environment Variables

Required in `.env`:

```bash
# Azure OpenAI (Required)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure AI Search (Required for RAG)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key

# Azure Cosmos DB (Required for state)
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-key

# Azure SQL Database (Required for segmentation)
AZURE_SQL_CONNECTION_STRING=Server=tcp:your-server.database.windows.net;Database=marketing_customers;...

# Application Insights (Optional)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Company Selection (Optional, default: hudson_street)
COMPANY_ID=hudson_street
```

---

## Security

- **Managed Identity** - DefaultAzureCredential for Azure services
- **No PII in responses** - Customer data is anonymized/aggregated
- **Content Safety** - Azure AI Content Safety validation
- **Brand Compliance** - Company-specific banned phrases and rules

---

## Support

For issues or questions, see documentation in `docs/` folder.
