<<<<<<< HEAD
# azure-ceo
=======
# Azure CEO (Customer Event Orchestrator)

Azure CEO is an Azure-native, multi-agent personalization engine transforming raw customer interactions into safe, on-brand personalized messages through Semantic Kernel orchestration and Azure AI services.

## Architecture Overview

```mermaid
flowchart TD
    A[CustomerEvent Ingested] --> B[Azure AI Language<br/>Sentiment + Enrichment]
    B --> C[Segmentation Agent<br/>Assign Segment + Reason]
    C --> D[Retrieval Agent<br/>Query Azure Cognitive Search]
    D --> E[Variant Generation Agent<br/>Azure OpenAI with Citations]
    E --> F[Safety Agent<br/>Azure Content Safety Check]
    F -->|Safe| G[Experiment/Uplift Agent<br/>A/B/n Assignment + Logging]
    F -->|Blocked| H[Safety Log<br/>Store Block Reason]
    G --> I[Personalized Message Delivered or Logged]
    H --> I
```

## Agents Architecture

```mermaid
flowchart LR
    subgraph Azure CEO Multi-Agent System
        SEG[Segmentation Agent]
        RET[Retrieval Agent]
        VAR[Variant Generation Agent]
        SAF[Safety Agent]
        UPL[Experiment/Uplift Agent]
    end
    SEG --> RET --> VAR --> SAF --> UPL
```

## Repo Structure

```plaintext
agents/
  segmentation_agent/
  retrieval_agent/
  variant_agent/
  safety_agent/
  uplift_agent/
orchestration/
connectors/
schemas/
api/
docs/
```

## License
Proprietary. See LICENSE.
>>>>>>> master
