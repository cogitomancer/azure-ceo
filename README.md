# Enterprise Multi-Agent Marketing Personalization System

A sophisticated multi-agent architecture for enterprise marketing automation, leveraging Azure AI, Semantic Kernel, and specialized AI agents to deliver compliant, data-driven, personalized marketing campaigns at scale.

## Quick Start

### 1. Setup Azure Services
Follow **[docs/AZURE_SETUP_GUIDE.md](docs/AZURE_SETUP_GUIDE.md)** to configure all required Azure services.

### 2. Install & Configure
```bash
# Clone repository
git clone <repository-url>
cd azure-ceo2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure service endpoints from AZURE_SETUP_GUIDE.md
```

### 3. Run Tests
Follow **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** to verify your setup.

### 4. Start Backend
```bash
uvicorn api.main:app --reload
```

### 5. Start Frontend
Follow **[docs/FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md)** to set up and run the React frontend.

---

## Architecture

### Agent Team
1. **Strategy Lead**: Orchestrates workflow, decomposes objectives
2. **Data Segmenter**: Queries Azure Synapse Analytics for audience analysis
3. **Content Creator**: Generates grounded marketing copy with citations via Azure AI Search
4. **Compliance Officer**: Validates content safety and brand compliance
5. **Experiment Runner**: Configures A/B/n tests and statistical analysis

### Azure Services
- **Azure OpenAI**: LLM provider (GPT-4o, GPT-4-turbo)
- **Azure Synapse Analytics**: Customer data warehouse
- **Azure AI Search**: RAG for content grounding
- **Cosmos DB**: State management
- **Azure App Configuration**: Feature flags
- **Azure AI Content Safety**: Content validation
- **Application Insights**: Monitoring

---

## Key Features

- **Grounded Content Generation**: All claims backed by citations from verified documents
- **Enterprise Governance**: Multi-layer safety filters and compliance validation
- **Automated Experimentation**: A/B/n test configuration with statistical analysis
- **Real-time Streaming**: Watch agents collaborate via Server-Sent Events
- **Beautiful Frontend**: React UI for campaign creation and management

---

## Documentation

### Essential Guides
- **[docs/AZURE_SETUP_GUIDE.md](docs/AZURE_SETUP_GUIDE.md)** ⭐ - Complete Azure service setup (Portal-based, no CLI required)
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing instructions and test suite overview
- **[docs/FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md)** - React frontend setup and usage

### Additional Documentation
- `docs/architecture.md` - System architecture and design patterns
- `docs/MODELS_USAGE.md` - AI models and usage information

---

## Configuration

### Agent Settings
Edit `config/agent_config.py` to customize agent personalities, models, and parameters.

### Safety Policies
Edit `config/safety_policies.yaml` to adjust safety thresholds.

### Brand Guidelines
Edit `config/brand_guidelines.yaml` to define brand voice and compliance rules.

---

## API Endpoints

- `POST /campaigns` - Create campaign (blocking)
- `POST /campaigns/stream` - Create campaign with real-time streaming
- `GET /campaigns` - List campaigns
- `GET /campaigns/:id` - Get campaign details
- `POST /content/validate` - Validate content safety
- `GET /health` - Health check

---

## Security

- Managed Identity authentication
- PII tokenization and redaction
- Multi-layer filter pipeline
- Audit logging for all actions
- RBAC for Azure services

---

## Support

For issues or questions:
- Email: azure-ceo-ai@gmail.com
- See documentation in `docs/` folder
