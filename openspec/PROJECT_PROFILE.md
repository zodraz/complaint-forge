# ComplaintForge Project Profile

**Scan Date:** 2026-06-18  
**Repository:** complaint-forge (git)  
**Status:** Existing brownfield project with spec-kit bootstrap in progress

---

## 🏗️ Tech Stack

| Category | Detected |
|----------|----------|
| **Primary Language** | Python 3.10+ (100% of backend code) |
| **Backend Framework** | FastAPI 0.115+ (REST API) |
| **Workflow Engine** | LangGraph 0.2+ (DAG-based complaint workflow) |
| **LLM Integration** | LangChain 0.3+, LangChain-OpenAI 0.2+ |
| **LLM Provider** | Azure OpenAI (via python-dotenv config) |
| **Agent Framework** | CrewAI 1.14+ (A2A specialist service) |
| **Observability** | LangSmith 0.1+ (optional tracing) |
| **ASGI Server** | Uvicorn 0.30+ (FastAPI server) |
| **API Schema** | Pydantic 2.9+ (request/response validation) |
| **External APIs** | Salesforce (OAuth 2.0), Zendesk (MCP client), Azure OpenAI (REST) |
| **Protocol Support** | MCP (Model Context Protocol) for Zendesk |
| **Containerization** | Docker (Dockerfile present) |
| **Orchestration** | Docker Compose (multi-service setup) |
| **HTTP Testing** | .http file format (complaint_forge.http) |
| **Package Manager** | pip (requirements.txt) |
| **Virtual Environment** | .venv/ (Python venv) |
| **Testing Framework** | Python unittest (standard library) |
| **Code Quality** | Not detected (no linting/type checking config visible) |

---

## 🏛️ Architecture Pattern

**Pattern Type:** Backend + Microservice with Human-in-the-Loop Workflow

**Structure:**
```
complaint-forge/
├── main_fastapi.py          # HTTP API layer (FastAPI)
├── graph.py                 # Workflow definition (LangGraph DAG)
├── agents/                  # LLM-driven agents (5 agents)
│   ├── triage.py            # Complaint classification
│   ├── analyzer.py          # Root cause analysis
│   ├── resolver.py          # Resolution proposal
│   ├── responder.py         # Customer response generation
│   └── action_agent.py      # Salesforce action execution
├── nodes/                   # Deterministic workflow nodes (6 nodes)
│   ├── customer_context.py  # Salesforce enrichment
│   ├── policy.py            # Policy validation
│   ├── guardrails.py        # Response quality evaluation
│   ├── specialist_review.py # A2A specialist integration
│   ├── human_review.py      # Human escalation interrupt
│   └── ignored.py           # Non-complaint routing
├── tools/                   # External service integrations (3 clients)
│   ├── salesforce_tool.py   # Salesforce CRM client
│   ├── zendesk_mcp_tool.py  # Zendesk MCP remote client
│   └── a2a_specialist_tool.py # A2A specialist service client
├── prompts/                 # LLM system prompts
│   └── system_prompts.py    # Centralized prompt definitions
├── response_evaluators.py   # Guardrails evaluation logic
├── llm_factory.py           # Azure OpenAI factory
├── config.py                # Configuration management
├── a2a_refund_specialist_service/  # Separate microservice
│   ├── app.py               # FastAPI specialist service
│   ├── llm_factory.py       # Specialist LLM config
│   └── requirements.txt     # Specialist dependencies
├── tests/                   # Unit & integration tests
├── .specify/                # Spec-kit configuration
├── openspec/                # Spec-kit artifacts
└── .github/                 # GitHub workflows & prompts
```

**Architecture Characteristics:**
- **Microservices**: 2 separate FastAPI apps (main + specialist service)
- **Workflow Engine**: LangGraph for orchestration (DAG-based)
- **Human-in-the-Loop**: LangGraph `interrupt()` mechanism for review escapes
- **Layered**: Agents (LLM logic) + Nodes (deterministic routing) + Tools (external integrations)
- **Event-Driven**: Zendesk webhooks trigger complaint workflow
- **State Management**: In-memory checkpointing (MemorySaver) for dev/test

---

## 📦 Module Map

| Module | Path | Type | Purpose | Dependencies |
|--------|------|------|---------|--------------|
| **HTTP API** | `main_fastapi.py` | Layer | REST endpoints, thread management | FastAPI, graph, tools |
| **Workflow Engine** | `graph.py` | Engine | DAG topology, routing logic | LangGraph, agents, nodes |
| **Triage Agent** | `agents/triage.py` | Agent | Classify complaints | LangChain, Azure OpenAI |
| **Analyzer Agent** | `agents/analyzer.py` | Agent | Root cause analysis | LangChain, Azure OpenAI |
| **Resolver Agent** | `agents/resolver.py` | Agent | Propose resolution | LangChain, Azure OpenAI |
| **Responder Agent** | `agents/responder.py` | Agent | Draft customer response | LangChain, Azure OpenAI |
| **Action Agent** | `agents/action_agent.py` | Agent | Execute Salesforce actions | LangChain, Azure OpenAI, Salesforce |
| **Customer Context Node** | `nodes/customer_context.py` | Node | Salesforce enrichment | Salesforce tool |
| **Policy Node** | `nodes/policy.py` | Node | Policy validation | (deterministic) |
| **Guardrails Node** | `nodes/guardrails.py` | Node | Response quality evaluation | response_evaluators |
| **Specialist Review Node** | `nodes/specialist_review.py` | Node | A2A specialist integration | a2a_specialist_tool |
| **Human Review Node** | `nodes/human_review.py` | Node | Escalation interrupt | LangGraph |
| **Ignored Node** | `nodes/ignored.py` | Node | Non-complaint routing | (deterministic) |
| **Salesforce Tool** | `tools/salesforce_tool.py` | Tool | CRM integration | requests, OAuth |
| **Zendesk MCP Tool** | `tools/zendesk_mcp_tool.py` | Tool | MCP remote client | mcp |
| **A2A Specialist Tool** | `tools/a2a_specialist_tool.py` | Tool | Specialist service client | requests |
| **LLM Factory** | `llm_factory.py` | Utility | LLM initialization | LangChain-OpenAI |
| **Specialist Service** | `a2a_refund_specialist_service/app.py` | Microservice | Specialist recommendation | FastAPI, CrewAI, LangChain |
| **Response Evaluators** | `response_evaluators.py` | Module | Guardrails logic | (LLM-based evaluation) |
| **Configuration** | `config.py` | Config | App settings | python-dotenv |

**Inter-Module Dependencies:**
- Main API (`main_fastapi.py`) → Graph (`graph.py`)
- Graph → Agents + Nodes
- Agents → LLM Factory
- Nodes → Tools + Response Evaluators
- Specialist Service → independent (called by specialist_review node via tool)

---

## 📋 Conventions Detected

### File Naming
- **Agents:** `snake_case.py` (e.g., `triage.py`, `analyzer.py`)
- **Nodes:** `snake_case.py` (e.g., `customer_context.py`, `policy.py`)
- **Tools:** `snake_case.py` (e.g., `salesforce_tool.py`)
- **Modules:** `snake_case.py` (e.g., `response_evaluators.py`)
- **Configuration:** `config.py`, `.env`, `.env.example`

### Directory Naming
- **Functional:** `agents/`, `nodes/`, `tools/`, `prompts/`, `tests/`
- **Service:** `a2a_refund_specialist_service/`
- **Configuration:** `.specify/`, `.github/`, `.venv/`

### Git History (Branch Pattern)
- Primary branch: `main` (seen in context)
- Upstream: `↑1` (ahead by 1 commit)

### Commit Style
- Not visible from current context; would need `git log --oneline -20` to confirm

### Testing Convention
- **Test Directory:** `tests/` (top-level)
- **Test Files:** Standard library `unittest` (not pytest)
- **Command:** `python -B -m unittest discover -s tests -v`

### Documentation Structure
- `README.md` — Project overview
- `AGENTS.md` — Architecture guide
- `.github/copilot-instructions.md` — Agent context
- `complaint_forge.http` — API examples (HTTP file format)

---

## 🏛️ Existing Governance

### ✅ Documented Standards
- ✅ **AGENTS.md** — Workflow architecture, naming rules, common pitfalls
- ✅ **README.md** — Project overview, workflow diagram
- ✅ **complaint_forge.http** — API testing examples
- ✅ `.github/copilot-instructions.md` — Agent context for GitHub Copilot

### ✅ Configuration Files
- ✅ **.gitignore** — Git exclusions (prevents __pycache__ tracking)
- ✅ **.env.example** — Template for environment variables
- ✅ **.dockerignore** — Docker build exclusions
- ✅ **Dockerfile** — Container image definition
- ✅ **docker-compose.yml** — Multi-service orchestration

### ⚠️ Missing/Incomplete Standards
- ❌ **.editorconfig** — No editor settings standardization
- ❌ **linting config** (no `.ruff.toml`, `.pylintrc`)
- ❌ **type checking config** (no `mypy.ini`, `pyproject.toml`)
- ❌ **CONTRIBUTING.md** — No contribution guidelines
- ❌ **ARCHITECTURE.md** — No architecture decision records
- ❌ **GitHub Actions CI/CD** — No workflow files detected
- ❌ **Testing config** — No `pytest.ini` (using unittest only)

### ✅ New Spec-Kit Integration
- ✅ **.specify/** — Spec-kit project structure
- ✅ **openspec/specs/** — Feature specifications (6 YAML files)
- ✅ **openspec/PLAN.md** — Implementation plan
- ✅ **.specify/memory/constitution.md** — Project constitution (v1.0.0)

---

## 📊 Project Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Agents** | 5 | Complete |
| **Total Nodes** | 6 | Complete |
| **Total Tools** | 3 | Complete |
| **HTTP Endpoints** | 6+ | Complete |
| **External Services** | 3 (Salesforce, Zendesk MCP, A2A) | Integrated |
| **Microservices** | 2 (main + specialist) | Complete |
| **Test Files** | 5 detected | Partial |
| **Python Files** | ~40+ | Complete |
| **Specifications** | 6 YAML | New |
| **Code Coverage** | Unknown | Not measured |
| **Linting** | Not configured | ❌ Missing |

---

## 🚀 Current Status Assessment

### What's Working
✅ Core workflow architecture (LangGraph DAG)  
✅ All agents and nodes implemented  
✅ All external integrations (Salesforce, Zendesk, A2A specialist)  
✅ FastAPI REST API with async support  
✅ Docker containerization  
✅ Spec-kit project initialization  

### What's Missing
❌ Code quality checks (linting, type checking)  
❌ Automated CI/CD pipeline  
❌ Test coverage measurement  
❌ Performance SLA monitoring  
❌ Architecture Decision Records (ADRs)  
❌ Deployment documentation  

### What's New
✨ 6 detailed specifications (workflow, agents, nodes, tools, API, config)  
✨ Comprehensive implementation plan (9 phases, 45+ tasks)  
✨ Project constitution (v1.0.0) with 4 core principles  
✨ Spec-kit configuration (templates, extensions, workflows)  

---

## 📈 Recommendations

### Phase 1: Governance & Quality (Short-term)
1. Add linting: `ruff`, `mypy --strict`
2. Configure code coverage: `coverage.py` with 85% minimum
3. Create GitHub Actions CI/CD pipeline
4. Add `.editorconfig` for editor consistency
5. Implement `CONTRIBUTING.md` guide

### Phase 2: Testing & Observability (Medium-term)
1. Increase test coverage to 85% minimum
2. Add integration tests for all workflow paths
3. Configure LangSmith tracing for debugging
4. Add performance monitoring (SLA tracking)
5. Document deployment procedures

### Phase 3: Documentation (Medium-term)
1. Create `ARCHITECTURE.md` with ADRs
2. Add API documentation (OpenAPI/Swagger)
3. Write deployment guide (dev, staging, prod)
4. Document system prompts and prompt engineering process

### Phase 4: Scalability & Reliability (Long-term)
1. Switch to PostgreSQL checkpointing (prod)
2. Implement distributed tracing
3. Add load balancing for multiple API instances
4. Set up monitoring and alerting (99.5% uptime SLA)
5. Create disaster recovery plan

---

## 📚 Key Files to Know

| File | Purpose | Priority |
|------|---------|----------|
| `main_fastapi.py` | API endpoints & state management | Critical |
| `graph.py` | Workflow DAG & routing | Critical |
| `agents/*.py` | LLM agents (5 files) | Critical |
| `nodes/*.py` | Deterministic nodes (6 files) | Critical |
| `tools/*.py` | External integrations (3 files) | Critical |
| `AGENTS.md` | Architecture documentation | High |
| `README.md` | Project overview | High |
| `.specify/memory/constitution.md` | Governance principles | High |
| `openspec/specs/*.yaml` | Feature specifications | High |
| `openspec/PLAN.md` | Implementation roadmap | High |
| `requirements.txt` | Dependencies | Medium |
| `docker-compose.yml` | Service orchestration | Medium |
| `.env.example` | Configuration template | Medium |
| `tests/` | Unit & integration tests | Medium |

---

## ✨ Next Steps (Using Spec-Kit)

1. **Run bootstrap validation:**
   ```bash
   specify.brownfield.bootstrap
   ```

2. **Generate tailored configuration:**
   - Use `speckit.brownfield.bootstrap` to validate project structure
   - Output will generate tailored spec-kit templates

3. **Generate implementation tasks:**
   ```bash
   specify tasks  # Generate tasks.md from existing specs
   ```

4. **Start implementation using constitution:**
   - All 4 constitution principles must be followed
   - 85% code coverage minimum required
   - TDD mandatory for new agents/nodes
   - See `.specify/memory/constitution.md` for full governance

---

**Scan Completed:** 2026-06-18  
**Project Status:** Ready for spec-kit bootstrap and implementation planning  
**Next Action:** Run `speckit.brownfield.bootstrap` to generate tailored configuration
