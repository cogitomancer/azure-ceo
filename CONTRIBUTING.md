# Contributing to Azure CEO

Thank you for your interest in contributing to Azure CEO — an Azure-native, multi-agent Customer Event Orchestrator.

This project is currently pre-alpha and under rapid development. PRs are welcome, but may be refactored as architecture evolves.

---

## Development Workflow

### 1. Clone the repo
git clone https://github.com/cogitomancer/azure-ceo.git

cd azure-ceo

### 2. Create a feature branch
git checkout -b feature/<name>

### 3. Follow the architecture
All agents, skills, and workflows must align with the core architecture under `/docs/architecture`.

### 4. Commit conventions
Use clear, atomic commits:
feat: add segmentation agent
fix: correct safety rule logic
docs: update README with badges
refactor: reorganize schema definitions

### 5. PR Guidelines
- All PRs must pass linting
- Include a short description of feature + screenshots if UI
- Link to related Issue
- Tag with `feature`, `fix`, or `docs`

---

## Code Style

### Python
- Black formatting
- Pydantic for schemas
- FastAPI as API layer
- Semantic Kernel for orchestration

### TypeScript (if adding UI)
- ESLint + Prettier
- React or Next.js

---

## Directory Structure
api/ # FastAPI app
agents/ # Multi-agent definitions
skills/ # Semantic Kernel skills
schemas/ # Pydantic models
connectors/ # Azure integrations
orchestration/ # Pipelines & workflows
docs/ # Architecture & diagrams

---

## License
This project is proprietary. Do not distribute derivative works without written permission from the maintainers.

---

## Contact
For major features: open an Issue and tag @cogitomancer.
