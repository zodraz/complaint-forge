# ComplaintForge Locust Scenarios

This folder contains load scenarios for the main FastAPI app in `main_fastapi.py`.

Start the API first:

```powershell
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

Run Locust with the web UI:

```powershell
locust -f locust/locustfile.py --host http://localhost:8000
```

Run a short headless smoke load:

```powershell
locust -f locust/locustfile.py --host http://localhost:8000 --headless -u 5 -r 1 -t 2m
```

The Locust user defines 100 named scenarios. They cover:

- FastAPI health, OpenAPI, and docs endpoints.
- Pending human-review list, detail, resume, unknown-thread, rejected-review, adjusted-resolution, and validation paths.
- Zendesk webhook ingestion with wrapped ticket payloads, direct ticket payloads, comment bodies, requester email variants, missing ticket ids, and validation failures.
- Complaint variants for missing orders, damaged products, wrong items, billing disputes, repeat contacts, angry customers, replacement requests, cancellation requests, address issues, missing parts, quality complaints, subscription issues, warranty claims, exchange requests, refund delays, account-credit gaps, partial deliveries, and delivered-not-received cases.
- Synchronous `/test/complaint` workflows for standard complaints, high-value escalation, non-complaints, validation failures, default email behavior, multiple-order complaints, high-value lost packages, low-value credits, formal complaints, and policy/guardrail-style edge language.

The `/test/complaint` scenarios run the LangGraph workflow inline and can call LLM,
Salesforce, Zendesk MCP, and A2A integrations depending on configuration. Their task
weights are intentionally lower than lightweight read and webhook scenarios.
