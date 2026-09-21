# Building ComplaintForge: An Autonomous AI Complaint Handler with LangGraph, CrewAI, and Human-in-the-Loop

---

## Introduction

Customer complaints are a high-stakes, high-volume problem for any business that touches real customers. Tickets pile up, response quality varies with agent fatigue, and escalations get lost. At the same time, the current generation of LLMs is genuinely good at reading context, proposing resolutions, and drafting empathetic responses — if you can constrain them with the right guardrails.

ComplaintForge is my attempt to wire these ideas together into a production-grade, autonomous complaint handling system. It ingests Zendesk tickets, enriches them with Salesforce CRM data, runs a chain of AI agents to triage, analyse, and resolve the complaint, enforces deterministic business rules and response quality guardrails, executes the approved CRM actions, and closes the ticket — all without a human touching it for the majority of cases.

When a complaint *does* need a human — high-value refunds, ambiguous policy cases, low-quality drafts — the workflow pauses cleanly at a LangGraph interrupt and hands a fully-enriched review packet to a support agent, complete with an AI specialist recommendation from a separate CrewAI-powered microservice.

This article walks through how it's built, the choices behind every major framework decision, the tooling used to develop it agentic-first, and what specifying features looks like in an AI-native workflow.

---

## Use Case

Imagine a mid-sized e-commerce business receiving 500–2,000 support tickets per day. A significant percentage are straightforward complaint patterns: delayed delivery, wrong item received, refund not processed. Each one requires the same sequence of steps:

1. Read and classify the ticket
2. Pull the customer's order and case history from the CRM
3. Decide what the right resolution is (refund, credit, replacement, escalate)
4. Check that the resolution doesn't breach any business rules
5. Draft a customer-facing response
6. Evaluate the response for quality and empathy
7. Execute the CRM action (log a case, create a task)
8. Update the ticket as solved

A human agent doing this well takes 5–15 minutes per ticket. Done poorly, it damages the customer relationship. Done at scale by a consistent AI system — with a human backstop for the edge cases — it can reliably resolve the majority of tickets in under a minute, with a quality floor that doesn't drift with agent mood or time-of-day.

ComplaintForge models exactly this workflow. The happy path is fully autonomous. The escalation path preserves human authority where it matters.

---

## Architecture

### C4

The system is documented using the [C4 model](https://c4model.com/diagrams) — a hierarchy of four diagram levels that describe the same system at increasing levels of detail: **Context → Container → Component → Code**.

**Context level** shows the two human personas (Support Agent and Operations Engineer), the external systems (Zendesk, Salesforce, Azure OpenAI, LangSmith, OpenTelemetry/New Relic), and the system boundary. Zendesk is both the ticket source (inbound webhook) and the update target (outbound via MCP).

**Container level** reveals two independently deployable services:
- `complaint-handler` — the main FastAPI + LangGraph workflow (port 8000)
- `a2a-specialist` — a CrewAI-powered FastAPI microservice for escalation reviews (port 8010)

**Component level** decomposes each container: the complaint handler splits into the HTTP API layer, the LangGraph workflow engine, the five LLM agents, the seven deterministic nodes, and the external integration tools. The specialist service is a self-contained CrewAI crew with a single agent and task.

**Code level** documents every module, function signature, and dependency — useful as a navigation aid when the codebase grows.

What's interesting about the C4 process in this project is that the documentation itself was generated agentic-ally, using the Claude Code C4 architecture plugin. More on that in the *Agentic Usage* section.

---

## Project Structure

```
complaint-forge/
├── main_fastapi.py          # FastAPI endpoints, thread management, human-review API
├── graph.py                 # LangGraph DAG topology and routing
├── agents/                  # Five LLM-driven agents
│   ├── triage.py
│   ├── analyzer.py
│   ├── resolver.py
│   ├── responder.py
│   └── action_agent.py
├── nodes/                   # Seven deterministic workflow nodes
│   ├── customer_context.py
│   ├── policy.py
│   ├── guardrails.py
│   ├── specialist_review.py
│   ├── human_review.py
│   ├── outbound_communication.py
│   └── ignored.py
├── tools/                   # External service clients
│   ├── salesforce_tool.py
│   ├── zendesk_mcp_tool.py
│   └── a2a_specialist_tool.py
├── prompts/
│   └── system_prompts.py
├── response_evaluators.py   # LLM-as-judge evaluators for guardrails
├── llm_factory.py           # Azure OpenAI / LiteLLM factory
├── otel.py                  # OpenTelemetry setup and helpers
├── config.py
├── a2a_refund_specialist_service/
│   ├── app.py
│   ├── llm_factory.py
│   └── otel.py
├── tests/
├── locust/
├── specs/                   # Feature specifications (SpecKit)
└── docker-compose.yml
```

The separation between `agents/` and `nodes/` is deliberate and enforced. Agents make LLM calls. Nodes are deterministic. This constraint keeps the graph topology readable and makes testing straightforward — nodes have no non-determinism to mock.

---

## Frameworks

### LangGraph

LangGraph is the orchestration engine for the complaint workflow. It models the process as a typed state graph — a `StateGraph[ComplaintState]` — where each node receives the full state, does its work, and returns a partial update.

```
triage → customer_context → analyzer → resolver → policy → responder → guardrails → action → communication
                                                       ↓                       ↓
                                              specialist_review         specialist_review
                                                       ↓                       ↓
                                               human_review            human_review
```

What LangGraph adds beyond a simple pipeline is conditional routing, checkpointing, and — critically — the `interrupt()` mechanism for human-in-the-loop pauses. When the policy or guardrails node sets `resolution_type = "escalate"`, the next node calls `interrupt(payload)`, which suspends the graph and persists its full state. The workflow can then be resumed later via `Command(resume=payload)` with the human's decision, picking up exactly where it left off.

This is powerful because the graph doesn't poll, doesn't timeout, and doesn't lose context. The human reviewer gets the complete enriched state — complaint text, customer history, specialist recommendation — and submits a single API call to resume.

For production, `MemorySaver` (in-process) would be replaced with PostgreSQL-backed checkpointing to survive restarts.

### CrewAI

The `a2a_refund_specialist_service` is a separate FastAPI microservice powered by CrewAI. It exposes an A2A-compatible endpoint (`POST /tasks/refund-specialist`) that receives the full escalation context and returns an advisory recommendation.

Inside, it runs a single-agent CrewAI crew:

```python
specialist = Agent(
    role="Refund and Escalation Specialist",
    goal="Review escalated complaint cases and prepare a concise, policy-aware recommendation for a human approver.",
    backstory="You are a senior support operations specialist. You do not execute refunds. You prepare evidence-based recommendations for humans.",
    llm=llm,
)
```

The key design choice here is that the specialist is **advisory only**. It never approves or executes anything. Its output goes into the human review packet alongside the full workflow context. This keeps accountability with the human reviewer, while giving them a structured, evidence-based starting point.

The service has a graceful fallback: if CrewAI fails to import (e.g., Python version incompatibility — CrewAI currently requires `<3.14`), it returns a safe fallback recommendation telling the reviewer to assess manually. The workflow never blocks on the specialist.

### Agents in ComplaintForge

Five LLM agents drive the workflow, each with a tightly scoped responsibility:

| Agent | Role | Temperature |
|---|---|---|
| **Triage** | Classifies the message as complaint or not; extracts email, phone, order ID | Low (0) |
| **Analyzer** | Identifies root cause, severity, urgency, sentiment | Low (0) |
| **Resolver** | Proposes resolution type (refund/credit/replacement/escalate) and amount | Low (0) |
| **Responder** | Drafts customer-facing email copy — empathetic, on-brand | Medium (0.7) |
| **Action Agent** | Decides which Salesforce action to execute based on the approved resolution | Low (0) |

Temperature zero for all decision-making agents keeps behaviour consistent and auditable. The Responder gets a slightly higher temperature to allow natural language variation in the drafted copy — customers notice when they all receive identical emails.

Each agent uses `system_prompts.py` for its instructions and structured output via Pydantic models, making it easy to test the output contract without requiring a live LLM call.

### A2A

ComplaintForge implements the Agent-to-Agent (A2A) protocol for inter-service communication between the main workflow and the specialist service. The specialist service exposes an agent card at `GET /.well-known/agent-card.json` that describes its capabilities, making it discoverable to other agents or orchestrators.

The main service calls the specialist via the A2A tool (`tools/a2a_specialist_tool.py`), which handles authentication (Bearer token), retry with exponential backoff (3 attempts), and translates HTTP failures into structured error payloads that the workflow can handle gracefully.

> For a deeper look at the A2A protocol and why it matters for multi-agent architectures, see the companion article on **FeedbackForge**, which covers A2A integration patterns in detail.

### Workflows

The full complaint workflow follows a strict sequence with two escalation escape hatches:

**Happy path** (fully autonomous):
1. Triage classifies and extracts structured metadata
2. Customer context enriches with Salesforce data (contact, account, recent cases, orders, return orders)
3. Analyzer identifies what went wrong and how serious it is
4. Resolver proposes the resolution
5. Policy gate applies hard deterministic rules (value thresholds, repeat customer rules, fraud signals)
6. Responder drafts the customer-facing message
7. Guardrails evaluate the draft for empathy (score ≥ 7) and resolution appropriateness (score ≥ 7) using LLM-as-judge evaluators
8. Action agent executes the Salesforce Case or Task
9. Communication node delivers the response via email (with SMS fallback) and closes the Zendesk ticket via MCP

**Escalation path** (human-in-the-loop):
- Triggered when policy flags a case (high value, repeat escalations, ambiguous resolution) or when guardrails score the draft too low
- Specialist review node calls the A2A CrewAI service for an advisory recommendation
- Human review node calls `interrupt()` — the graph pauses
- Support agent reviews via `GET /review/{thread_id}` and resumes via `POST /review/{thread_id}/resume`
- Workflow picks up from the communication node, sends the human-approved response, closes the ticket

### Observability

#### LangSmith

LangSmith provides LLM-level tracing: every `llm.invoke()` call across all five agents is captured with its input prompt, output, token count, and latency. This is invaluable for debugging unexpected resolutions — you can trace exactly which prompt produced which decision and why.

Tracing is optional and controlled entirely via environment variables (`LANGSMITH_TRACING=true`). When disabled, zero overhead. In production, traces are routed to the EU endpoint (`eu.api.smith.langchain.com`) for data residency.

#### New Relic (OTEL)

Both services use a shared `otel.py` module that wires up the full OpenTelemetry SDK — traces, metrics, and logs — all exported via OTLP HTTP to a collector (New Relic in production). This gives infrastructure-level visibility that complements LangSmith's LLM-level view.

```python
setup_otel("complaintforge-complaint-handler")
```

One call at startup configures:
- `TracerProvider` with `BatchSpanProcessor` → `OTLPSpanExporter`
- `MeterProvider` with `PeriodicExportingMetricReader` → `OTLPMetricExporter`
- `LoggerProvider` with `BatchLogRecordProcessor` → `OTLPLogExporter`
- Auto-instrumentation for `requests` and `logging`
- `FastAPIInstrumentor` for automatic HTTP request spans

Custom business metrics — `complaint.completed`, `complaint.pending_review`, `review.resumed`, `a2a.crewai_success` — are recorded as histograms, making it trivial to build SLA dashboards in New Relic: how many complaints resolved per minute, what percentage required human review, how often the CrewAI specialist succeeded versus falling back.

The `@function_trace()` decorator wraps individual functions in their own spans, so a waterfall trace shows exactly how long each external call took: Salesforce OAuth → SOQL query → A2A specialist → Zendesk MCP update.

---

## Integrations

ComplaintForge talks to four external systems: Salesforce as the CRM of record, Zendesk as the ticketing layer, Mailchimp Transactional for customer-facing delivery, and the A2A specialist service for escalation review. Each integration lives in its own file under `tools/`, with a deliberate boundary: nothing outside that file knows how the integration works, only what it returns.

### Salesforce

Salesforce is the integration that does the most work. It's used at two separate points in the workflow with completely different purposes.

At the **enrichment stage** (`nodes/customer_context.py`), the tool runs four SOQL queries in sequence against the Salesforce REST API:

1. Find the Contact by email — gives us contact ID, account ID, phone
2. Fetch the five most recent Cases for that contact — complaint history
3. Fetch the five most recent Opportunities for the account — customer value context
4. Find the matched Order by order number, or fall back to the most recent order on the account
5. Fetch recent Return Orders linked to the account or order

This enriched context flows into every downstream agent as `customer_history`. The Analyzer uses it to flag repeat complaints. The Resolver uses it to weight the resolution. The Policy node uses it to decide whether a matched order exists before approving a refund. A contact not found in Salesforce is not an error — it returns a structured `{"error": "Contact not found"}` that the Policy node catches and escalates.

At the **action stage** (`agents/action_agent.py`), the tool writes back to Salesforce based on the approved resolution:

| Resolution | Salesforce action |
|---|---|
| `full_refund` / `partial_refund` | Creates a high-priority Case |
| `credit` | Creates a standard Case |
| `replacement` | Creates a Task for the fulfilment team |

Authentication uses the OAuth2 client credentials flow — a short-lived access token is fetched at the start of each call. There's no token caching, which means one extra round-trip per operation, but it avoids stale-token failures and keeps the implementation stateless.

```python
response = requests.post(
    SALESFORCE_LOGIN_URL + "/services/oauth2/token",
    data={
        "grant_type": "client_credentials",
        "client_id": SALESFORCE_CLIENT_ID,
        "client_secret": SALESFORCE_CLIENT_SECRET,
    },
)
access_token, instance_url = payload["access_token"], payload["instance_url"]
```

SOQL injection is prevented by a `_soql_string()` helper that escapes backslashes and single quotes before interpolating any user-supplied value into a query string. Object and field names from environment variables are validated against an alphanumeric-plus-underscore allowlist before being used in queries.

### Zendesk via MCP

Zendesk ticket updates use the **Model Context Protocol (MCP)** rather than the Zendesk REST API directly. This is the most architecturally interesting integration in the project.

The MCP client (`tools/zendesk_mcp_tool.py`) connects to a remote MCP Streamable HTTP server, negotiates a session, and calls a named tool — `update_ticket` by default, configurable via `ZENDESK_MCP_UPDATE_TICKET_TOOL`. The tool receives ticket ID, target status, the final response text as a comment, and a workflow summary (triage result, resolution, actions taken).

```python
async with streamable_http_client(ZENDESK_MCP_URL, http_client=http_client) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(ZENDESK_MCP_UPDATE_TICKET_TOOL, arguments=payload)
```

Using MCP here rather than a direct API call has a concrete benefit: the Zendesk integration can be swapped, extended, or replaced by updating the MCP server — the workflow code doesn't change. Any system that exposes an MCP tool with the right signature can slot in. This pattern is increasingly common in agentic architectures: the agent-facing interface is stable, the implementation behind it is replaceable.

If `ZENDESK_MCP_URL` is not configured, the node skips the update and logs a warning — no exception, no crash. The ticket remains in its pre-workflow state, which is a recoverable situation. If the MCP call fails after the workflow has already executed Salesforce actions, the actions are not rolled back — the system is designed to be eventually consistent, not transactional.

### Mailchimp Transactional

Customer responses are delivered through Mailchimp Transactional (`tools/mailchimp_tool.py`) using the official Python SDK. The integration handles both email and SMS, with SMS as an automatic fallback when email delivery fails permanently.

The key design in this tool is the failure taxonomy. Not all delivery failures are equal:

| Response | Classification | Consequence |
|---|---|---|
| `sent` / `queued` | success | Done |
| `rejected` (4xx Mailchimp error) | `permanent_failure` | Triggers SMS fallback |
| 5xx / 429 (rate limit) | `transient_failure` | Returned for retry logic upstream |

A permanently-failed email — a bounced address, a domain that doesn't exist, a blocked sender — won't succeed on retry, so triggering SMS immediately is the right call. A transient failure (Mailchimp's servers are momentarily unavailable) is different: retrying makes sense. Collapsing these into a single "error" state would force either always-retry (wasteful on permanent failures) or never-retry (loses valid sends on transient ones).

Emails support an optional `correlation_id` that gets embedded in Mailchimp's metadata field. This enables idempotency checks — if the outbound communication node is re-executed (e.g., after a workflow resume), the same correlation ID prevents a duplicate send from reaching the customer.

```python
if correlation_id:
    message["metadata"] = {"correlation_id": correlation_id}
```

Both `send_email` and `send_sms` return structured dicts rather than raising exceptions. Every failure mode — missing config, missing SDK, rejected send, API exception — produces a `{"status": ..., "provider": "mailchimp", "provider_response": {...}}` payload that the caller can inspect without a try/except. This keeps the communication node's error handling in one place and makes the tool straightforward to test with simple assertions on the return value.

---

## Deployment

Both services are containerised. The root `Dockerfile` builds the main complaint handler; `a2a_refund_specialist_service/Dockerfile` builds the specialist. `docker-compose.yml` wires them together for local development and integration testing.

Production deployment targets **Azure Container Apps** (ACA) in the `northeurope` region. ACA handles scaling, ingress, and managed TLS without requiring Kubernetes expertise.

### Deploy Skill (Agent Deploy — A2A)

The deploy process is exposed as a Claude Code skill, meaning a single command from the IDE triggers the full deployment sequence: build the container image, push to Azure Container Registry, update the ACA revision, and validate the health endpoint. The skill understands both containers — you can deploy the main handler, the A2A specialist, or both in one invocation.

This is a good example of the broader pattern in this project: wherever a multi-step process needs to be repeatable and auditable, it gets wrapped as an agent skill rather than a shell script. The skill can reason about the current state (are there uncommitted changes? is the health check passing?), ask for confirmation before touching production, and record what it did.

---

## Foundry

ComplaintForge's LLM layer is powered by **Azure AI Foundry** — Microsoft's platform for deploying, managing, and monitoring Azure OpenAI models. The deployment (`AZURE_OPENAI_DEPLOYMENT_NAME`) maps to a model endpoint managed in Foundry, making it straightforward to swap model versions (GPT-4o, GPT-4o mini) or adjust quota without changing application code.

The `llm_factory.py` supports a second mode via **LiteLLM** — a lightweight proxy that normalises OpenAI-compatible APIs across providers. With `USE_LITELLM=true` and a `LITELLM_BASE_URL` pointing at your proxy, the same code can route to Anthropic, Gemini, or local Ollama models. This proved useful during development: running the full workflow against a cheaper, faster model for iteration, then switching to the production model for quality checks — without touching a single line of agent code.

```python
def get_chat_llm(*, temperature: float = 0) -> ChatOpenAI:
    if USE_LITELLM:
        return ChatOpenAI(model=LITELLM_MODEL, base_url=LITELLM_BASE_URL, ...)
    return ChatOpenAI(model=AZURE_OPENAI_DEPLOYMENT_NAME, base_url=_azure_openai_base_url(), ...)
```

---

## LiteLLM

LiteLLM is an open-source proxy that presents a unified OpenAI-compatible interface in front of every major LLM provider — Azure OpenAI, Anthropic, Gemini, Mistral, local Ollama, and more. In ComplaintForge, it sits between the application and the model endpoint: the application code stays identical regardless of which provider is behind it.

### Switching models with a single env flag

The integration is minimal by design. Setting `USE_LITELLM=true` and pointing `LITELLM_BASE_URL` at your proxy is enough to redirect every LLM call through it:

```env
USE_LITELLM=true
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=sk-1234
LITELLM_MODEL=gpt-4o-mini
```

The `llm_factory.py` factory reads these variables and constructs a `ChatOpenAI` client aimed at the proxy instead of Azure directly. No agent code changes required.

This proved useful during development: running the full five-agent workflow against `gpt-4o-mini` for rapid iteration kept costs low, then switching `LITELLM_MODEL` to the production deployment for quality validation. The same mechanism works for testing against Anthropic or a local model without touching the application.

### Spend tracking and budget limits

The most-used LiteLLM feature in this project wasn't the multi-provider routing — it was the built-in **spend tracking and budget controls**.

LiteLLM's proxy maintains a running cost ledger per API key, per virtual team, and per model. Every request is priced at real-world rates and recorded in the proxy's database. The dashboard shows a live cost breakdown: how much each model has consumed, which call patterns are driving the spend, and where the budget is going.

For ComplaintForge — which fires five LLM calls per complaint through triage, analysis, resolution, response drafting, and action planning — this matters. During Locust load tests at 50 concurrent users, per-request cost compounds quickly across model iterations and it's easy to lose track of cumulative spend.

The budget controls close that gap. You attach a `max_budget` and a `budget_duration` to a virtual API key:

```json
{
  "max_budget": 10.00,
  "budget_duration": "1d",
  "model": "azure/gpt-4o"
}
```

Once the key hits its ceiling, the proxy returns a `BudgetExceededError` rather than silently accumulating charges. You can set separate ceilings per environment — tight for local development, higher for staging, alert-only for production — and the proxy enforces them without any application-level logic.

For a workflow with a predictable cost structure (N agents × M tokens per complaint), this made it straightforward to validate the per-complaint unit cost against the business case before scaling the load tests up.

---

## Testing

### Unit Tests

Tests use Python's standard-library `unittest` — no pytest, no additional frameworks. Each module has a corresponding test file:

```
tests/
├── test_triage.py
├── test_nodes.py
├── test_main_fastapi.py
├── test_a2a_specialist_service.py
├── test_a2a_specialist_tool.py
├── test_salesforce_tool.py
├── test_outbound_communication.py
└── test_prompts.py
```

The strategy is to mock LLM calls and external APIs at the boundary, then test the logic of each node and agent independently. Because agents and nodes have a strict separation (agents make LLM calls; nodes are deterministic), most node tests require no mocking at all.

```powershell
python -B -m unittest discover -s tests -v
```

The `-B` flag skips bytecode generation — the repo previously had tracked `__pycache__` files and this prevents re-introducing them.

### Load Testing with Locust

The `locust/locustfile.py` provides a Locust-based load test suite that simulates realistic traffic patterns against the running API. It models multiple user scenarios weighted by realistic frequency:

| Scenario | Weight | Description |
|---|---|---|
| Health check | 15x | Background monitoring traffic |
| Submit complaint | 8x | Standard complaint submission |
| High-value refund (escalation) | 2x | Triggers the human-review path |
| List pending reviews | 8x | Support agent polling |
| Resume review | 3x | Human reviewer submitting decisions |
| OpenAPI schema fetch | 3x | Tooling and integration clients |

The test tracks `PENDING_REVIEW_IDS` in a shared queue — escalated complaints are stored as they arrive, so resume scenarios can reference real thread IDs from the same load-test session. This makes the escalation flow a genuine end-to-end load test, not a synthetic exercise.

```powershell
locust --host http://localhost:8000 -f locust/locustfile.py --headless -u 50 -r 5
```

---

## Agentic Usage

ComplaintForge was built using Claude Code throughout development — not just as a code completion tool, but as an active collaborator in architecture, specification, and documentation.

### Claude C4 Agents

The C4 architecture documentation was generated entirely using the **Claude Code C4 Architecture plugin** (`wshobson/agents` marketplace). The plugin registers four specialised subagents — `c4-code`, `c4-component`, `c4-container`, and `c4-context` — each tuned to their level of the C4 hierarchy.

Invoking `/c4-architecture:c4-architecture` launched a multi-phase workflow:

- **Phase 1 (Code level):** 8 agents ran in parallel, one per source directory (`agents/`, `nodes/`, `tools/`, `prompts/`, `tests/`, `locust/`, `a2a_refund_specialist_service/`, root). Each agent read the actual source files and produced a `c4-code-*.md` documenting every function signature, parameter type, return type, and dependency.

- **Phase 2 (Component level):** 4 component agents synthesised the code docs into logical components — Complaint Handler API, External Integrations, A2A Specialist Service, Testing Infrastructure — followed by a master index agent that produced a Mermaid relationship diagram.

- **Phase 3 (Container level):** A container agent read the component docs, `docker-compose.yml`, and both Dockerfiles, then produced `c4-container.md` plus OpenAPI 3.1 YAML specifications for both services.

- **Phase 4 (Context level):** A context agent — informed by the README, AGENTS.md, full source context, and the container docs — produced `c4-context.md` with personas, user journeys, external systems, and a Mermaid C4Context diagram.

14 agents, three sequential phases, all writing to `C4-Documentation/`. The entire documentation set — 4,800 lines — was generated in under 15 minutes. The intermediate result hit a model access error (the `c4-code` agent type defaulted to `claude-haiku-4-5` which wasn't available), which was fixed by editing the workflow script file and resuming from the cached run ID — only the failed agents re-ran, the completed ones returned cached results instantly.

This is one of the more compelling demonstrations of what multi-agent orchestration enables: a documentation task that would take a senior engineer a full day was reduced to a single command, with each agent working in parallel and the results synthesised bottom-up.

---

## SpecKit

SpecKit is a lightweight feature specification workflow for AI-native codebases. Rather than writing tickets in Jira, each feature starts as a structured spec in `specs/<feature-name>/` — a directory containing a canonical spec, data model, implementation plan, test checklists, and quickstart guide.

### 001-outbound-communication

The outbound communication feature (`specs/001-outbound-communication/`) is a good example of how SpecKit shapes development. The spec defines the feature in terms of actors, user scenarios, and **testable functional requirements** — not vague acceptance criteria:

> *"The node must distinguish between transient and permanent email failures (configurable thresholds) and treat permanent failures as immediate triggers for SMS fallback. Test: Simulate error responses and assert fallback behaviour."*

From the spec, SpecKit generates:
- **`data-model.md`** — the `CommunicationPayload`, `DeliveryAttempt`, and `DeliveryRecord` entities with their state transitions (EmailAttempted → EmailSucceeded → DeliveredEmail; or → PermanentFailure → SmsAttempted → DeliveredSms)
- **`plan.md`** — a phased implementation plan tied to the project's tech stack and architecture constraints
- **`tasks.md`** — discrete tasks derived from the functional requirements
- **`checklists/`** — pre-implementation and post-implementation review gates
- **`quickstart.md`** — how to run the tests for this specific feature in isolation

This spec-first approach has a concrete payoff when working with AI coding agents. Instead of describing the feature in a chat prompt, you point the agent at `specs/001-outbound-communication/spec.md` and `plan.md`. The agent has structured, unambiguous context — no hallucinated requirements, no missed edge cases, no contradiction between what was asked and what was built.

The feature itself implements a `nodes/outbound_communication.py` node that delivers the final response via Mailchimp Transactional Email (with SMS fallback via Mailchimp SMS), records a `DeliveryRecord` in the workflow trace, and emits OTLP events for every delivery attempt.

---

## Vibe Coding

A lot of ComplaintForge was built with what the community has started calling "vibe coding" — describing intent at a high level and letting the AI figure out the implementation details. It works surprisingly well for this kind of project, where the architecture is well-defined and the patterns repeat.

What actually makes it work isn't the LLM's raw capability — it's the scaffolding around it. `AGENTS.md` functions as a constitution for the codebase: naming rules, which file owns what, which patterns are forbidden. When Claude Code has that context loaded, it doesn't drift. It generates a new node in `nodes/`, not `agents/`. It doesn't add HubSpot integrations because the file explicitly says Salesforce is the CRM. It uses `@function_trace()` from `otel.py` because that's the pattern in every other file.

The SpecKit specs serve the same function for feature development: they pre-decide the data model, the error taxonomy, the test contract, and the performance SLAs, so the coding session starts with all the ambiguity resolved. The agent writes code; the human owns the decisions.

The real discipline is in what you *don't* let the agent do. Early versions of this project accumulated a coordinator agent, HubSpot and Stripe integrations, and an event bus that nobody asked for. The `AGENTS.md` file is partly a historical record of those mistakes — "do not reintroduce a coordinator agent unless it truly coordinates the whole workflow", "do not add HubSpot or Stripe back" — captured as durable instructions that survive context resets.

That's the model: the human maintains the constitution, the specs define the features, the agent writes the code. It's fast, it's auditable, and it scales in a way that pure vibe coding — typing ideas into a chat box and hoping for the best — doesn't.

---

*ComplaintForge is available as a reference implementation. The C4 documentation, SpecKit specs, and deployment skill are all included in the repository. If you're building an agentic workflow on LangGraph and want a working example of human-in-the-loop, A2A inter-service communication, and production observability, it's a good place to start.*

---

## Lessons Learnt

### 1. Separate agents from nodes from the start — don't let it drift

The clearest structural decision in this codebase is the hard line between `agents/` (LLM calls) and `nodes/` (deterministic logic). It sounds obvious, but it's easy to let a node quietly grow an LLM call for "just one edge case". Once that happens, testing becomes painful — you can no longer test that node without mocking an LLM. Enforce the boundary early, document it in your `AGENTS.md`, and don't negotiate with it.

### 2. The human interrupt is the most important node

Everything else in the workflow is optimising the happy path. The `human_review` interrupt is the safety net that makes it safe to automate the happy path at all. Design it first, not last. What data does the reviewer actually need? How does the resume payload map back to the workflow state? Get this right before you build the agents, not after.

### 3. CrewAI and LangGraph don't need to be in the same process

Running the CrewAI specialist as a separate microservice (A2A) turned out to be one of the best decisions in the architecture. It decouples Python version constraints (CrewAI requires `<3.14`), lets the service scale independently, and means a CrewAI failure never crashes the main workflow. If you're mixing frameworks, separate them at the network boundary.

### 4. MemorySaver is fine for development; plan your checkpointing strategy before production

It took a support call to remember that `MemorySaver` state disappears on restart. In development, losing a pending review on restart is an inconvenience. In production, it's data loss. The migration to PostgreSQL-backed checkpointing requires changing one line in `graph.py`, but the schema design and migration strategy take real thought. Don't leave it to the week before go-live.

### 5. LLM-as-judge guardrails add real value, but calibrate your thresholds empirically

The empathy and resolution-appropriateness evaluators in `response_evaluators.py` were added to catch obviously bad agent outputs before they reach customers. They work — they've caught several mis-scored resolutions during testing. But the score thresholds (≥ 7/10 to proceed) were initially guesses. Run the evaluators against a representative sample of past tickets and tune the thresholds to match your actual quality floor, not a number that sounds reasonable.

### 6. Dual observability (LangSmith + OTEL) covers different failure modes

LangSmith tells you *why* an agent made the wrong decision (the prompt, the context it saw, the token distribution). OTEL tells you *what happened* at the infrastructure level (the Salesforce call took 4.2s, the A2A specialist timed out, the MCP connection dropped). You need both. Routing them through the same `otel.py` helper keeps the setup cost low.

### 7. AGENTS.md is worth more than you think

When you work with AI coding agents over months, context windows reset constantly. Every reset is a potential for drift — the agent rediscovers patterns you already decided against and reintroduces them. The `AGENTS.md` file, loaded as persistent context, functions as institutional memory. Every time you catch an agent doing something wrong, add it to the file. "Do not add HubSpot or Stripe back", "Use `get_chat_llm` not direct `AzureChatOpenAI`", "Zendesk updates go through MCP only" — these one-liners have each saved significant refactoring time.

### 8. Spec first, code second

Writing the outbound communication spec before writing a line of code exposed three assumptions that would have caused rework: the idempotence requirement (same correlation ID → no duplicate sends), the dual-failure path (both email and SMS fail → human review interrupt, not silent failure), and the configurability requirement (retry counts and provider selection must be env-configurable, not hardcoded). All three would have been harder to retrofit. Specs are cheap; retrofits are expensive.

### 9. Vibe coding needs a constitution to stay coherent

Unguided vibe coding generates fast the first time and creates debt the second time. The pattern that actually works: human owns the decisions (architecture, data models, error taxonomy, performance contracts), AI owns the implementation. The spec-first workflow + `AGENTS.md` + `CLAUDE.md` is the mechanism that keeps those roles clear across sessions, across models, and across team members.

### 10. Multi-agent documentation generation is genuinely useful

The C4 documentation workflow wasn't a novelty — it produced documentation that I wouldn't have written manually, at a level of detail that's actually useful for onboarding. The code-level docs with full function signatures are the kind of thing that always gets deferred until it never happens. Automating it removes the deferral. If you have a complex codebase and a documentation deficit, running a structured multi-agent documentation workflow is one of the highest-leverage things you can do with an afternoon.
