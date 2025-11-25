# Enterprise Multi-Agent Marketing Personalization System

## Overview

This system implements a sophisticated multi-agent architecture for enterprise marketing automation, 
leveraging Azure AI Foundry, Semantic Kernel, and specialized AI agents to deliver compliant, 
data-driven, personalized marketing campaigns at scale.

## Architecture

### Layer 1: Infrastructure
- **Azure AI Foundry**: Unified AI platform with private endpoints and managed identities
- **Azure OpenAI**: LLM provider (GPT-4o for complex reasoning, GPT-3.5-Turbo for simple tasks)
- **Azure AI Search**: Vector store for RAG-based content grounding
- **Cosmos DB**: State management and conversation persistence
- **Azure App Configuration**: Feature flag management for A/B tests
- **Azure AI Content Safety**: Pre-send validation and compliance
- **Azure Monitor**: Comprehensive observability and tracing

### Layer 2: Orchestration
- **Semantic Kernel**: Agent coordination framework
- **AgentGroupChat**: Multi-agent collaboration pattern
- **Process Framework**: Long-running campaign workflows
- **Filter Pipeline**: Multi-layer governance guardrails

### Layer 3: Agent Team
1. **Strategy Lead (Manager)**: Orchestrates workflow, decomposes objectives
2. **Data Segmenter**: Queries CDP, performs audience analysis
3. **Content Creator**: Generates grounded marketing copy with citations
4. **Compliance Officer**: Safety validation and brand compliance
5. **Experiment Runner**: A/B/n test configuration and statistical analysis

### Layer 4: Integration
- **CDP Plugins**: Adobe Real-Time CDP, Databricks
- **RAG Plugins**: Azure AI Search text retrieval
- **Safety Plugins**: Content Safety API wrappers
- **Experiment Plugins**: App Configuration SDK, statistical analysis

### Layer 5: Security & Governance
- **Three Lines of Defense**: System prompts, reviewer agents, hard filters
- **Private Endpoints**: Secure communication within Azure backbone
- **Managed Identity**: Keyless authentication
- **PII Protection**: Tokenization and redaction
- **Audit Logging**: Complete traceability

## Quick Start

### Prerequisites
- Azure subscription with required services provisioned
- Python 3.10+
- Azure CLI

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/marketing-agent-system.git
cd marketing-agent-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure service endpoints
```

### Running the System

```bash
# Run main application
python main.py

# Or use CLI
python -m cli.main campaign create --objective "Your campaign goal"
```

## Key Features

### 1. Grounded Content Generation
- All product claims backed by citations from verified documents
- RAG implementation via Azure AI Search
- Automatic citation extraction and formatting

### 2. Enterprise Governance
- Pre-send safety validation via Azure AI Content Safety
- Multi-layer filter pipeline (prompt safety, function authorization, PII redaction)
- Independent compliance officer agent for content review

### 3. Automated Experimentation
- A/B/n test configuration via Azure App Configuration
- Statistical significance calculation (z-test, p-values, confidence intervals)
- Dynamic traffic allocation with kill switch capability

### 4. Data Privacy
- PII tokenization and redaction
- Anonymized user IDs only in agent context
- Audit logging for all data access

## Configuration

### Agent Configuration
Edit `config/agent_config.py` to customize agent personalities, models, and parameters.

### Safety Policies
Edit `config/safety_policies.yaml` to adjust safety thresholds and compliance rules.

### Brand Guidelines
Edit `config/brand_guidelines.yaml` to define brand voice, tone, and custom compliance rules.

## Deployment

### Docker
```bash
docker build -t marketing-agents .
docker run -p 8000:8000 --env-file .env marketing-agents
```

### Kubernetes
```bash
kubectl apply -f deployment/kubernetes/
```

### Terraform (Infrastructure)
```bash
cd deployment/terraform
terraform init
terraform plan
terraform apply
```

## Monitoring & Observability

Access Azure Monitor dashboards to track:
- Agent reasoning and decision paths
- Token usage and costs per agent
- Campaign performance metrics
- Safety violations and compliance issues

## Testing

```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Generate coverage report
pytest --cov=. --cov-report=html
```

## Security Considerations

1. **Never commit secrets**: Use Azure Key Vault or managed identities
2. **Network isolation**: All services behind private endpoints
3. **RBAC**: Implement least-privilege access controls
4. **Audit trails**: All agent actions logged and traceable
5. **Regular security reviews**: Monitor for new threat patterns

## License

Proprietary - Enterprise License

## Support

For issues or questions:
- Email: azure-ceo-ai@gmail.com