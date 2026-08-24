# C4 Component Level: ComplaintForge Master Index

## System Components

| Component | Short Description | Documentation |
|---|---|---|
| Complaint Handler API | Central complaint-processing service: FastAPI webhook intake, LangGraph multi-agent workflow, human-review REST API, and full OpenTelemetry + LangSmith observability. | [c4-component-complaint-handler-api.md](./c4-component-complaint-handler-api.md) |
| External Integrations | Client adapters encapsulating every outbound HTTP call — Salesforce (CRM), Zendesk (via MCP), A2A Refund Specialist, and Mailchimp (email/SMS) — with OAuth 2.0 auth, retry logic, and error normalisation. | [c4-component-external-integrations.md](./c4-component-external-integrations.md) |
| A2A Refund Specialist Service | Standalone FastAPI microservice that accepts escalated complaint packages, runs a CrewAI specialist agent, and returns a policy-aware refund/credit recommendation via the A2A protocol. | [c4-component-a2a-specialist-service.md](./c4-component-a2a-specialist-service.md) |
| Testing Infrastructure | unittest + asyncio unit/integration test suite (eight modules, all collaborators mocked) and a Locust load-test suite (100 weighted HTTP task scenarios) covering all pipeline stages and API endpoints. | [c4-component-testing-infrastructure.md](./c4-component-testing-infrastructure.md) |

---

## Component Relationships Diagram

```mermaid
C4Component
    title ComplaintForge — Master Component Relationships

    Container_Boundary(main_api, "Complaint Handler API — port 8000") {
        Component(complaint_handler, "Complaint Handler API", "Python / FastAPI / LangGraph / LangChain", "Webhook intake, 12-node LangGraph workflow, human-review REST API, LLM agent pipeline, OTel and LangSmith observability")
        Component(ext_integrations, "External Integrations", "Python / requests / httpx / mcp / mailchimp-transactional", "Outbound HTTP adapters for Salesforce, Zendesk MCP, A2A Specialist, and Mailchimp; handles OAuth 2.0, retry, and error normalisation")
    }

    Container_Boundary(a2a_svc, "A2A Refund Specialist Service — port 8001") {
        Component(a2a_specialist, "A2A Refund Specialist Service", "Python / FastAPI / CrewAI", "Single-crew CrewAI specialist agent for escalated complaint review; A2A discovery endpoint; three-layer fallback guarantee")
    }

    Container_Boundary(testing, "Testing Infrastructure") {
        Component(test_infra, "Testing Infrastructure", "Python / unittest / asyncio / Locust / Docker", "Unit and async integration tests with full mock isolation; Locust HTTP load suite with 100 weighted scenarios")
    }

    System_Ext(salesforce, "Salesforce", "CRM SaaS — customer history lookups and refund, credit, replacement-order record creation")
    System_Ext(zendesk, "Zendesk", "Helpdesk SaaS — ticket status updates and public agent comments via MCP Streamable HTTP")
    System_Ext(azure_openai, "Azure OpenAI", "LLM inference backend for all agent, evaluator, and specialist reasoning calls")
    System_Ext(langsmith, "LangSmith", "LLM run tracing and offline quality evaluation for the complaint pipeline")
    System_Ext(otel_collector, "OTel Collector", "Receives OTLP/HTTP traces, metrics, and logs from both running services")

    Rel(complaint_handler, ext_integrations, "Delegates all outbound calls — customer history, CRM actions, email/SMS, Zendesk ticket close, specialist escalation")
    Rel(ext_integrations, a2a_specialist, "POST /tasks/refund-specialist (3-attempt linear-backoff retry)", "HTTPS / A2A JSON")

    Rel(test_infra, complaint_handler, "Imports and patches modules under test; sends weighted concurrent HTTP requests via Locust", "Python unittest.mock / HTTP")
    Rel(test_infra, a2a_specialist, "Imports and patches app, llm_factory, and otel modules under test", "Python unittest.mock")

    Rel(complaint_handler, azure_openai, "LLM inference — triage, analysis, resolution, response drafting, guardrail evaluation", "HTTPS / OpenAI REST")
    Rel(complaint_handler, langsmith, "LLM run traces and quality evaluation scores", "HTTPS / LangSmith API")
    Rel(complaint_handler, otel_collector, "Exports distributed traces, histogram metrics, and logs", "OTLP/HTTP")

    Rel(ext_integrations, salesforce, "OAuth 2.0 token acquisition, SOQL queries, Case and Task creation", "HTTPS / Salesforce REST API")
    Rel(ext_integrations, zendesk, "Invokes update_ticket MCP tool via Streamable HTTP session", "MCP Streamable HTTP / Bearer token")

    Rel(a2a_specialist, azure_openai, "LLM inference for specialist agent reasoning", "HTTPS / OpenAI REST")
    Rel(a2a_specialist, otel_collector, "Exports distributed traces, histogram metrics, and logs", "OTLP/HTTP")
```
