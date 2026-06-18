# ComplaintForge Constitution

**Project**: Autonomous Complaint Handling System with LangGraph + LangSmith  
**Purpose**: Establish non-negotiable governance principles for development, testing, UX, and performance

---

## Core Principles

### I. Code Quality & Maintainability (Non-Negotiable)

Every line of code in ComplaintForge must prioritize clarity, correctness, and long-term maintainability.

**Requirements:**
- All code must be self-documenting: function names must clearly describe intent, complex logic must include inline comments
- Strict type hints on all functions (Python 3.10+); no `Any` types without explicit justification in comments
- Maximum cyclomatic complexity of 5 per function; break down complex logic into smaller, testable units
- All agent/node implementations must follow the explicit pattern: inputs → processing → outputs (no side effects except in final action node)
- Code review mandatory for all PRs; minimum 1 approval required before merge
- Linting required: use `ruff check` for style, `mypy` for type checking (strict mode)

**Rationale:** ComplaintForge processes customer complaints affecting revenue and trust. Code defects directly harm customer experience and company reputation. High code quality prevents cascading failures.

---

### II. Testing Standards (Non-Negotiable)

Test-Driven Development (TDD) is mandatory. Coverage requirements strictly enforced.

**Requirements:**
- Minimum 85% code coverage for all agent/node implementations (measured via `coverage.py`)
- Unit tests written BEFORE implementation; Red-Green-Refactor cycle strictly enforced
- All external dependencies (Salesforce, Zendesk, Azure OpenAI) must have mock tests and integration tests
- Every agent outputs must be validated against schema in tests (no "trust the LLM" approach)
- Integration tests required for all workflow paths: success path, policy escalation, guardrail escalation, human review resume
- Timeout tests mandatory: all external service calls must test for timeout scenarios with exponential backoff
- All tests run in CI/CD pipeline before merge; no green CI allowed with test failures

**Test Command Standard:**
```bash
python -B -m unittest discover -s tests -v  # Run all tests
coverage run -m unittest discover -s tests  # Generate coverage
coverage report --fail-under=85             # Enforce 85% minimum
```

**Rationale:** Complaints are time-sensitive and costly. Test coverage prevents regressions, ensures reliability, and gives confidence in prod deployments.

---

### III. User Experience Consistency (Non-Negotiable)

All customer-facing outputs (responses, error messages, status messages) must be consistent, empathetic, and professional.

**Requirements:**
- **Response Tone Standards**: All customer responses must be empathetic, non-blaming, and action-oriented. Violate this standard → human review escalation.
- **Response Structure**: Every response must include: acknowledgment of issue, explanation of root cause (without blame), resolution offered, next steps with timeline, contact information
- **Clarity Standards**: Responses must use plain language (avoid jargon); max 3 sentences per paragraph; active voice preferred
- **Consistency across channels**: Whether responding via email, Zendesk, or API callback, tone and content must be identical
- **Human-in-the-Loop for edge cases**: Any response flagged as potentially harmful, unclear, or off-brand must escalate to human review (responder → guardrails → specialist_review → human_review)
- **A/B Testing**: All response variations must be tracked and compared for customer satisfaction metrics

**Guardrails Enforcement:**
- Factuality score must be ≥ 0.7 (hallucination detection via response_evaluators)
- Tone score must be ≥ 0.7 (empathy/professionalism detection)
- Clarity score must be ≥ 0.7 (readability/completeness check)
- Any score < 0.7 triggers human review

**Rationale:** Customers are frustrated by complaints. Poor UX (unclear responses, cold tone, missing next steps) extends resolution time and damages trust. Consistency builds confidence.

---

### IV. Performance & Reliability Standards (Non-Negotiable)

ComplaintForge must handle complaints within predictable latency SLAs and never lose state.

**Requirements:**
- **Latency SLAs**:
  - Triage: ≤ 2 seconds (classification only)
  - Analyzer + Resolver: ≤ 15 seconds per step
  - Responder: ≤ 10 seconds
  - Guardrails: ≤ 5 seconds
  - Total happy path (no escalation): ≤ 45 seconds
  - With human review: ≤ 24 hours (SLA reset on human action)

- **Availability**: 99.5% uptime for API endpoints (Zendesk webhook, status polling, human review resume)
- **Timeout Handling**: All external service calls (Salesforce, Azure OpenAI, A2A specialist) must have explicit timeouts:
  - Salesforce: 10s per call, max 3 retries with exponential backoff
  - Azure OpenAI: 30s per call, max 2 retries
  - A2A Specialist: 30s, max 3 retries
  - Zendesk MCP: 20s per call, non-blocking failure (workflow completes even if MCP unavailable)

- **State Persistence**: All complaint state must be checkpointed after every node; in-memory MemorySaver for dev/test, PostgreSQL for production
- **Concurrent Workflows**: Must support ≥ 100 simultaneous complaints without performance degradation
- **Memory Usage**: Workflow state + context must not exceed 5MB per complaint; garbage collection after workflow completion
- **Error Recovery**: All failures must be recoverable; no data loss on service restart; human review resume must work even after process crash

- **Monitoring**: All LLM calls traced to LangSmith; all external service calls logged with latency; alerting on SLA violations

**Performance Tests (Required):**
- Load test: 100 concurrent complaints, measure p95 latency
- Stress test: 500 concurrent complaints, track error rates
- Long-running test: 10,000 sequential complaints over 24 hours, monitor memory leaks

**Rationale:** Customers' problems compound over time. Slow resolution damages satisfaction. High availability and reliability prevent data loss and rebuild customer trust.

---

## Architecture Constraints

### Agent/Node Pattern (Enforced)
- **Agents** (in `agents/`): Pure LLM-driven; stateless; deterministic temperature settings per use case
- **Nodes** (in `nodes/`): Deterministic logic; routing; external integrations; no LLM calls except specialist_review
- **No side effects before guardrails**: Salesforce actions only after policy + guardrails pass
- **Human-in-the-loop escalations**: All escalations pause workflow and wait for human decision; never auto-resume without approval

### External Service Integration (Enforced)
- All Salesforce operations isolated to `tools/salesforce_tool.py`
- All Zendesk updates isolated to `tools/zendesk_mcp_tool.py`
- All A2A specialist calls isolated to `tools/a2a_specialist_tool.py`
- All LLM calls routed through `llm_factory.get_chat_llm()` with Azure OpenAI config
- System prompts centralized in `prompts/system_prompts.py`

### API Contract (Enforced)
- All POST endpoints return 202 Accepted for async workflows
- All GET endpoints include thread_id, status, interrupts, current state
- All error responses include error code, message, and trace_id for debugging
- All request bodies validated via Pydantic BaseModel

---

## Development Workflow

### Code Review Gate
1. Author submits PR with tests passing locally
2. Linting and type checking must pass: `ruff check`, `mypy --strict`
3. Coverage must be ≥ 85%: `coverage report --fail-under=85`
4. Minimum 1 approval from code owner (agent lead or senior engineer)
5. All CI checks must pass before merge

### Testing Gate
- Unit tests required for all new agents and nodes
- Integration tests required for workflow changes
- Manual testing required for LLM-driven components (tone, clarity, response quality)
- Performance tests required for any changes to latency-critical paths

### Deployment Gate
1. All tests passing in CI/CD
2. Code review approved
3. Staging deployment verified (test with sample data)
4. Performance baseline verified (SLAs checked)
5. Monitoring/alerting configured
6. Rollback plan documented

---

## Quality Metrics & Enforcement

**Compliance Checks:**
- Code coverage: `coverage report --fail-under=85` (fails if < 85%)
- Linting: `ruff check` must have zero errors (warnings acceptable)
- Type checking: `mypy --strict` must have zero errors
- Test execution: `python -B -m unittest discover -s tests -v` must pass all tests
- Performance: p95 latency must not exceed SLA thresholds (measured in integration tests)

**Metrics to Track:**
- Code coverage trend (target: ≥ 85%, no regression)
- SLA violations (target: < 1% of workflows exceed latency SLA)
- Human review escalation rate (target: < 10% of complaints; track trend)
- Guardrails escalation rate (target: < 5% of complaints; track trend)
- Response satisfaction score (A/B testing results; target: ≥ 4.0/5.0)
- Mean time to resolution (target: ≤ 4 hours for non-escalated)

**Enforcement:**
- All PRs blocked if coverage < 85%
- All PRs blocked if linting or type checking fails
- All deployments blocked if SLA violations detected in staging
- Quarterly governance review: metrics presented, constitution updated if needed

---

## Governance

### Constitution Authority
This constitution supersedes all other practices, conventions, and documented preferences. In case of conflict, this document is the source of truth.

### Amendment Process
1. **Proposal**: Document change with rationale, impact analysis, migration plan
2. **Discussion**: Present to engineering team; minimum 48 hours for feedback
3. **Approval**: Majority vote of team leads
4. **Documentation**: Update constitution with version bump (see versioning below)
5. **Migration**: Implement changes with sunset period for old practices (minimum 1 sprint)
6. **Communication**: Notify all stakeholders; update developer docs

### Versioning Policy
- **MAJOR**: Backward incompatible principle removals or redefinitions (e.g., dropping test coverage requirement)
- **MINOR**: New principles or materially expanded guidance (e.g., adding a new SLA metric)
- **PATCH**: Clarifications, wording changes, non-semantic refinements (e.g., fixing a typo)

### Compliance Review
- **Weekly**: Spot-check 1-2 recent PRs for compliance with code quality, testing standards
- **Monthly**: Review metrics dashboard; assess performance SLA adherence
- **Quarterly**: Full governance review; propose constitution amendments if needed; update CLAUDE.md and AGENTS.md to reflect any changes

---

## Development Guidance

**For detailed runtime guidance (environment setup, local testing, deployment commands), see:**
- [CLAUDE.md](../CLAUDE.md) — Agent-specific context and best practices
- [AGENTS.md](../AGENTS.md) — Workflow architecture, naming rules, common pitfalls

**For specifications and planning, see:**
- `openspec/specs/` — Detailed feature specifications
- `openspec/PLAN.md` — Implementation phases and checklists

**This constitution defines WHAT we do and WHY. Those documents define HOW we do it.**

---

## Ratification & Amendment History

| Version | Ratified | Last Amended | Status |
|---------|----------|--------------|--------|
| 1.0.0 | 2026-06-18 | 2026-06-18 | Active |

<!-- When amending, append a row above with new version, date, and status -->

---

**Constitution Version**: 1.0.0  
**Ratified**: 2026-06-18  
**Last Amended**: 2026-06-18  
**Status**: Active
