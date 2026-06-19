# Implementation Plan: Outbound Communication

**Branch**: `feature/001-outbound-communication` | **Date**: 2026-06-19 | **Spec**: [specs/001-outbound-communication/spec.md](specs/001-outbound-communication/spec.md)

**Input**: Feature specification from `/specs/001-outbound-communication/spec.md`

**Project**: ComplaintForge LangGraph + LangSmith complaint handling system

## Summary

Implement an `outbound-communication` node that delivers responder output to customers via email (SendGrid) and falls back to SMS (Twilio) on permanent SendGrid bounces. The node will be a `nodes/outbound_communication.py` deterministic node called from the workflow after `responder` and `policy` checks; it will record `DeliveryRecord` in the workflow trace and emit audit logs.

## Technical Context

**Language/Version**: Python 3.10+ (typed with strict mypy mode)

**Primary Stack**:
- FastAPI 0.115+ (REST API)
- LangGraph 0.2+ (workflow orchestration)
- LangChain 0.3+ (LLM abstractions)
- Azure OpenAI (LLM provider)
- Pydantic 2.9+ (validation)
- LangSmith 0.1+ (tracing, optional)

**Testing Framework**: Python `unittest` (standard library) + `coverage.py` for 85% minimum

**Integrations**:
- Salesforce CRM (OAuth 2.0)
- Zendesk (MCP remote client)
- A2A specialist service (separate FastAPI app)

**Target Architecture**:
- **Agents** (in `agents/`): LLM-driven, stateless, deterministic temperature per use case
- **Nodes** (in `nodes/`): Deterministic routing, no LLM calls except specialist_review
- **Tools** (in `tools/`): External service clients with error handling

**Performance Goals**:
- Triage: ≤ 2s, Analyzer/Resolver: ≤ 15s per step, Responder: ≤ 10s
- Total happy path: ≤ 45s, With human review: ≤ 24h
- 99.5% uptime SLA for API endpoints

**Constraints**:
- No side effects before guardrails pass
- Salesforce actions only after policy + guardrails validation
- All external calls must have explicit timeouts + retry logic
- State must be checkpointed after every node
- Code coverage ≥ 85%, cyclomatic complexity ≤ 5 per function

**Scale**:
- ≥ 100 concurrent workflows supported
- Max 5MB state per complaint
- Latency SLAs strictly enforced

## Constitution Check

GATE: Verify non-negotiable rules in `.specify/memory/constitution.md` are satisfied.

- Language, typing, testing, and integration patterns conform to the constitution.
- No side effects will occur before guardrails/policy nodes (node is a post-guardrails action node).

Result: PASS — No constitution violations identified in the spec.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**ComplaintForge Functional Layout:**

```text
complaint-forge/
├── main_fastapi.py              # HTTP API layer (endpoints, thread management)
├── graph.py                     # LangGraph DAG (workflow topology)
├── llm_factory.py               # Azure OpenAI LLM factory
├── response_evaluators.py       # Guardrails evaluation logic
├── config.py                    # Configuration management
│
├── agents/                      # LLM-driven agents (5 files)
│   ├── triage.py                # Complaint classification
│   ├── analyzer.py              # Root cause analysis
│   ├── resolver.py              # Resolution proposal
│   ├── responder.py             # Customer response generation
│   └── action_agent.py          # Salesforce action execution
│
├── nodes/                       # Deterministic workflow nodes (6 files)
│   ├── customer_context.py      # Salesforce enrichment
│   ├── policy.py                # Policy validation
│   ├── guardrails.py            # Response quality evaluation (async)
│   ├── specialist_review.py     # A2A specialist integration
│   ├── human_review.py          # Human escalation interrupt
│   └── ignored.py               # Non-complaint routing
│
├── tools/                       # External service integrations (3 files)
│   ├── salesforce_tool.py       # Salesforce CRM client
│   ├── zendesk_mcp_tool.py      # Zendesk MCP remote client
│   └── a2a_specialist_tool.py   # A2A specialist service client
│
├── prompts/                     # LLM system prompts
│   └── system_prompts.py        # Centralized prompt definitions
│
├── a2a_refund_specialist_service/  # Separate microservice
│   ├── app.py                   # FastAPI specialist service
│   ├── llm_factory.py           # Specialist LLM config
│   └── requirements.txt         # Specialist dependencies
│
├── tests/                       # Unit & integration tests
│   ├── test_agents.py           # Agent tests (mock external services)
│   ├── test_nodes.py            # Node tests (workflow state)
│   ├── test_main_fastapi.py     # API endpoint tests
│   ├── test_tools.py            # Tool integration tests
│   └── test_[feature].py        # Feature-specific tests
│
├── requirements.txt             # Main dependencies
├── Dockerfile                   # Container image
├── docker-compose.yml           # Multi-service orchestration
├── .env.example                 # Configuration template
└── .gitignore                   # Git exclusions
```

**Feature Implementation Guidelines**:
- **If Agent**: Create in `agents/[name].py`, use `llm_factory.get_chat_llm()`, set temperature per use case
- **If Node**: Create in `nodes/[name].py`, no LLM calls (except specialist_review), implement error handling
- **If Tool**: Create in `tools/[name].py`, include timeout + retry logic, document auth/config
- **If Endpoint**: Add route to `main_fastapi.py`, validate via Pydantic, return 202 for async ops
- **If Tests**: Add to `tests/test_[feature].py`, aim for 85%+ coverage, mock external services
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
