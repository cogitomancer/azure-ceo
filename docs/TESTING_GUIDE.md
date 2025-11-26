# Testing Guide - Azure Marketing Agent System

## Overview

This guide explains how to test the multi-agent marketing system, including orchestration, individual agents, plugins, filters, and end-to-end workflows.

## Test Structure

```
tests/
├── integration/
│   ├── conftest.py                    # Shared fixtures
│   ├── test_kernel_factory_integration.py  # Kernel and Azure services
│   ├── test_orchestration.py         # Basic orchestration tests
│   └── test_complete_system.py       # COMPREHENSIVE test suite ⭐
├── unit/
│   ├── test_agents.py                 # Legacy - merged into integration
│   ├── test_plugins.py                # Legacy - merged into integration
│   └── test_filters.py                # Legacy - merged into integration
└── pytest.ini                         # Pytest configuration
```

## Quick Reference

**Required for Basic Tests:**
- Azure OpenAI (endpoint + deployment)
- Cosmos DB (endpoint + key)
- Azure App Configuration (endpoint)
- Application Insights (connection string)

**Optional (Tests will skip gracefully if not configured):**
- Azure AI Search (for RAG plugin)
- Azure Synapse Analytics (for data segmentation)
- Azure AI Content Safety (for content validation)

## Running Tests

### 1. Setup Environment

First, ensure your `.env` file is configured. See [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md) for complete setup.

Minimum required configuration:

```bash
# Required for all tests
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Required for kernel factory tests
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_APP_CONFIG_ENDPOINT=https://your-appconfig.azconfig.io
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Required for plugin tests (optional for basic tests)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX=product-docs
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/

# Optional - tests will skip gracefully if not configured
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX=product-docs
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_SYNAPSE_ENDPOINT=https://your-synapse.dev.azuresynapse.net
AZURE_SYNAPSE_DATABASE=marketing_dwh
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### 3. Run Tests

#### Test Kernel Factory (First Step)
Tests that Azure services are properly configured and Semantic Kernel is created:

```bash
pytest tests/integration/test_kernel_factory_integration.py -v -s
```

Expected output:
```
✓ Kernel created successfully
✓ Azure OpenAI service configured
✓ Cosmos DB service configured
✓ App Configuration service configured
✓ Azure Monitor configured
```

#### Test Orchestration (Second Step)
Tests that orchestrator and agents are properly initialized:

```bash
pytest tests/integration/test_orchestration.py -v -s
```

Expected output:
```
✓ Orchestrator initialized successfully
✓ All 5 agents created
✓ Group chat configured
✓ State manager integrated
```

#### Test Complete System (Recommended - Third Step)
**This is the comprehensive test suite that covers everything:**

```bash
pytest tests/integration/test_complete_system.py -v -s
```

This test suite covers:
- ✅ **Orchestration**: Workflow execution, state management
- ✅ **All 5 Agents**: StrategyLead, DataSegmenter, ContentCreator, ComplianceOfficer, ExperimentRunner
- ✅ **Plugins**: RAG, Synapse, Metrics, Content Safety, Brand Compliance
- ✅ **Filters**: Prompt Safety, Function Authorization
- ✅ **Utilities**: Citation Extractor
- ✅ **Error Handling**: Session IDs, edge cases

#### Run All Integration Tests

```bash
pytest tests/integration/ -v -s
```

#### Run Specific Test Class

```bash
# Test only agents
pytest tests/integration/test_complete_system.py::TestAgentsIntegration -v -s

# Test only plugins
pytest tests/integration/test_complete_system.py::TestPluginsIntegration -v -s

# Test only filters
pytest tests/integration/test_complete_system.py::TestFiltersIntegration -v -s
```

### 4. Run End-to-End Tests (Long Running)

The complete workflow tests are skipped by default. Enable them for full validation:

```bash
# This will execute a full campaign through all 5 agents
pytest tests/integration/test_complete_system.py::TestWorkflowIntegration -v -s
```

⚠️ **Warning**: This test takes several minutes as it calls Azure OpenAI APIs for each agent.

## Test Workflow Order

Follow this order for systematic testing:

### Phase 1: Infrastructure ✅ (Already Completed)
```bash
pytest tests/integration/test_kernel_factory_integration.py -v -s
```
Validates: Azure services, Kernel creation, Service configurations

### Phase 2: Orchestration ⭐ (Current Focus)
```bash
pytest tests/integration/test_orchestration.py -v -s
```
Validates: Orchestrator initialization, Agent setup, Group chat

### Phase 3: Individual Components
```bash
pytest tests/integration/test_complete_system.py::TestAgentsIntegration -v -s
pytest tests/integration/test_complete_system.py::TestPluginsIntegration -v -s
pytest tests/integration/test_complete_system.py::TestFiltersIntegration -v -s
```

### Phase 4: End-to-End (Optional)
```bash
pytest tests/integration/test_complete_system.py::TestWorkflowIntegration -v -s
```

## Understanding the Agent Workflow

The orchestrator uses **SequentialSelectionStrategy** which calls agents in order:

```
User Request (CEO Objective)
    ↓
1. StrategyLead
   - Analyzes objective
   - Creates campaign strategy
   - Plans execution steps
    ↓
2. DataSegmenter
   - Queries Azure Synapse Analytics for audience
   - Identifies target segment
   - Calculates segment size
    ↓
3. ContentCreator
   - Generates message variants (A/B/C)
   - Retrieves product info via RAG
   - Includes citations
    ↓
4. ComplianceOfficer
   - Validates content safety
   - Checks brand compliance
   - Verifies citations
   - Outputs: APPROVED or REJECTED
    ↓
5. ExperimentRunner
   - Creates feature flag in App Config
   - Sets up A/B/n test
   - Configures traffic allocation
   - Outputs experiment ID
    ↓
Result: Complete Campaign
```

## Plugin Requirements and Configuration

### RAG Plugin (retrieve_product_info)
**Required Azure Service**: Azure AI Search
**Configuration**:
```env
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX=product-docs
```

**Setup Steps**:
1. Create Azure AI Search resource
2. Create semantic search index
3. Upload product documentation
4. Configure semantic ranker

**Test Status**: Initialization tested, full functionality requires Azure AI Search

### Synapse Plugin (query_customer_segments, get_segment_details)
**Required Service**: Azure Synapse Analytics (see [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md))
**Configuration**:
```env
AZURE_SYNAPSE_ENDPOINT=https://your-synapse.dev.azuresynapse.net
AZURE_SYNAPSE_DATABASE=marketing_dwh
```

**Test Status**: Initialization tested, full functionality requires Synapse setup

### Metrics Plugin (calculate_significance)
**Status**: ✅ Fully functional - no external dependencies

### Content Safety Plugin (analyze_content_safety)
**Required Azure Service**: Azure AI Content Safety
**Configuration**:
```env
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=optional-if-using-rbac
```

**Test Status**: Initialization tested

### Brand Compliance Plugin (validate_brand_compliance)
**Status**: ✅ Fully functional - uses local brand_guidelines.yaml

## Filter Testing

### Prompt Safety Filter
Tests:
- Prompt injection detection
- PII detection (email, phone, SSN)
- Jailbreak attempts

Status: ✅ All tests passing

### Function Authorization Filter
Tests:
- Agent permission matrix
- High-risk function controls
- Wildcard permissions

Status: ✅ All tests passing

## Expected Test Results

### Passing Tests ✅
- Kernel factory initialization
- All 5 agents creation
- Group chat configuration
- State manager integration
- Metrics plugin calculations
- Brand compliance checks
- All filter validations

### Conditional Tests ⚠️
These tests pass initialization but may skip full functionality:
- RAG plugin (requires Azure AI Search)
- Synapse plugin (requires Azure Synapse Analytics)
- Content Safety plugin (requires Azure Content Safety)

### Skipped Tests 🚫
- End-to-end workflow tests (long-running, enable manually)

## Troubleshooting

### Issue: "Azure OpenAI endpoint not configured"
**Solution**: Verify `AZURE_OPENAI_ENDPOINT` in `.env`

### Issue: "Cosmos DB connection failed"
**Solution**: 
1. Check `COSMOS_DB_ENDPOINT` in `.env`
2. Verify Azure credentials (DefaultAzureCredential)
3. Ensure RBAC permissions are assigned

### Issue: "RAG plugin initialization failed"
**Expected**: RAG requires Azure AI Search setup (optional for basic tests)
**Action**: See "Next Azure Steps" section below

### Issue: "Synapse plugin initialization failed"
**Expected**: Synapse requires Azure Synapse Analytics setup (optional for basic tests)
**Action**: Configure Azure Synapse Analytics (see [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md)) or use mock data for testing

## Azure Service Setup

For complete Azure service setup, see **[AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md)**.

Required services:
- Azure OpenAI (for Semantic Kernel)
- Cosmos DB (for state management)
- Azure App Configuration (for feature flags)
- Application Insights (for monitoring)
- Azure Synapse Analytics (for customer data)
- Azure AI Search (for RAG)
- Azure AI Content Safety (for content validation)

## Frontend Integration

The API is ready for React frontend integration:

### Endpoints Available

#### 1. Create Campaign (Blocking)
```javascript
POST /campaigns
{
  "name": "Welcome Campaign",
  "objective": "Create welcome email for new customers",
  "created_by": "user@example.com"
}
```

#### 2. Create Campaign with Streaming (Recommended)
```javascript
// Use Server-Sent Events for real-time agent updates
const eventSource = new EventSource('/campaigns/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'agent_message') {
    console.log(`${data.agent_name}: ${data.content}`);
    // Update UI with agent response
  }
  
  if (data.event === 'completed') {
    console.log('Campaign completed!');
    eventSource.close();
  }
};
```

#### 3. Get Campaign Status
```javascript
GET /campaigns/{session_id}
```

#### 4. Health Check
```javascript
GET /health
```

### CORS Configuration
Already configured to accept all origins for development. Update for production:
```python
allow_origins=["https://your-frontend-domain.com"]
```

## Test Coverage Summary

| Component | Tests | Status |
|-----------|-------|--------|
| Kernel Factory | 7 tests | ✅ Passing |
| Orchestration | 6 tests | ✅ Passing |
| Agents (5 total) | 5 tests | ✅ Passing |
| Plugins (5 total) | 5 tests | ⚠️ Conditional |
| Filters (2 total) | 2 tests | ✅ Passing |
| Utilities | 1 test | ✅ Passing |
| Workflows | 1 test | 🚫 Skipped (manual) |
| **Total** | **27 tests** | **23 passing, 3 conditional, 1 skipped** |

## Next Steps

1. ✅ **Run Orchestration Tests** (Current)
   ```bash
   pytest tests/integration/test_orchestration.py -v -s
   ```

2. ✅ **Run Complete System Tests**
   ```bash
   pytest tests/integration/test_complete_system.py -v -s
   ```

3. ⚠️ **Configure Optional Azure Services** (see [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md))
   - Azure AI Search (for RAG)
   - Azure Content Safety (for compliance)
   - Azure Synapse Analytics (for segmentation)

4. 🚫 **Run End-to-End Tests** (Optional - Long Running)
   ```bash
   pytest tests/integration/test_complete_system.py::TestWorkflowIntegration -v -s
   ```

5. 🎨 **Build React Frontend**
   - Use streaming endpoint for real-time updates
   - Display agent messages as they're generated
   - Show campaign status and results

## Notes

- **Citation Plugin TODO**: Current implementation uses utility class. Consider refactoring to dedicated plugin for better agent integration. See `utils/citation_extractor.py` for details.

- **Test Duration**: Basic tests run in seconds. Full e2e tests take 2-5 minutes depending on agent complexity.

- **Mock Data**: For tests requiring external APIs (CDP, Azure Search), the system gracefully handles missing configurations and logs warnings.

## Support

For issues or questions:
1. Check `.env` configuration matches [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md)
2. Verify Azure RBAC permissions
3. Review test output logs
4. See [FRONTEND_SETUP.md](FRONTEND_SETUP.md) for frontend integration

