---
description: "Tasks for Outbound Communication implementation"
---

# Tasks: Outbound Communication

**Input**: Design documents in `specs/001-outbound-communication/`

## Phase 1: Setup & Test Infrastructure (FOUNDATIONAL)

- [X] T001 Create test file: `tests/test_outbound_communication.py` with imports and base test class
- [ ] T002 [P] Add test mocks for Mailchimp in `tests/mocks/mailchimp_mock.py` following SendGrid and Twilio mock patterns
- [ ] T003 [P] Add test fixtures for sample `CommunicationPayload` and `DeliveryRecord` in `tests/fixtures/communication_fixtures.py`
- [ ] T004 Configure coverage enforcement in `.coveragerc` and update `requirements.txt` with `coverage`
- [ ] T005 Validate `.gitignore` excludes `__pycache__` and test artifacts

**Checkpoint**: Test infra ready — tests should be written before implementation

## Phase 2: Tests for Outbound Communication (MANDATORY - Write FIRST)

- [X] T006 [P] Unit test: validate `CommunicationPayload` schema and missing-recipient validation in `tests/test_outbound_communication.py`
- [X] T007 [P] Unit test: email send success path (mock Mailchimp) in `tests/test_outbound_communication.py`
- [X] T008 [P] Unit test: email permanent bounce handling triggers SMS fallback (mock Mailchimp for both channels)
- [ ] T009 [P] Unit test: idempotence — repeated calls with same `correlation_id` do not duplicate sends
- [ ] T010 [P] Unit test: audit logging writes `DeliveryAttempt` entries to workflow trace (mock trace storage)
- [ ] T011 Integration test: end-to-end flow with mocked services — email success path results in `delivered_email` final_status
- [ ] T012 Integration test: email bounce → SMS fallback results in `delivered_sms` final_status

**Checkpoint**: Tests written and failing before implementation

## Phase 3: Implementation (P1)

### Tools (external clients)

- [X] T013 Create `tools/mailchimp_tool.py` with: `send_email()` and `send_sms()` functions, timeout config, and retry scaffolding
- [X] T014 [P] (Combined with T013) Both email and SMS use same Mailchimp tool
- [X] T015 [P] Add required config entries to `config.py` and `.env.example`: `MAILCHIMP_API_KEY`, `MAILCHIMP_SERVER_PREFIX`, `MAILCHIMP_FROM_EMAIL`, `MAILCHIMP_TIMEOUT`

### Node Implementation

- [X] T016 Create `nodes/outbound_communication.py` node with entry `def run(context, payload: CommunicationPayload) -> DeliveryRecord` and docstring
- [X] T017 [P] Implement call to `tools/mailchimp_tool.send_email()` with proper request mapping and timeout handling
- [X] T018 Implement Mailchimp response classification: treat permanent bounces as permanent failures and trigger SMS fallback
- [X] T019 [P] Implement SMS fallback using `tools.mailchimp_tool.send_sms()` when bounce detected and `recipient_phone` present
- [X] T020 Implement idempotence/dedup: check existing `DeliveryRecord` by `correlation_id` and skip duplicate sends
- [ ] T021 [P] Implement audit logging: append `DeliveryAttempt` objects to the workflow trace and persist `DeliveryRecord` in-memory/trace
- [X] T022 Add explicit error handling: on dual failure (email + SMS), emit human-review interrupt via existing `nodes/human_review.py` interrupt contract

### Endpoint (optional integration)

- [ ] T023 Create API route in `main_fastapi.py`: POST `/communications` -> validate `CommunicationRequest` model, enqueue workflow, return `202 Accepted` with `thread_id` and `status_url`
- [ ] T024 [P] Ensure endpoint uses Pydantic `CommunicationRequest` (as specified in contracts/communication_api.md)

### Types & Validation

- [X] T025 [P] Add Pydantic models for `CommunicationPayload`, `DeliveryAttempt`, and `DeliveryRecord` in a new module `nodes/communication_models.py` (or reuse `data-model` location)

**Checkpoint**: Node and tools implemented, run unit tests

## Phase 4: Quality Assurance & Integration

- [ ] T026 Run linting: `ruff check` and fix any issues for added files (`nodes/outbound_communication.py`, `tools/*`)
- [ ] T027 Run type checking: `mypy --strict` for new modules
- [ ] T028 Run all tests: `python -B -m unittest discover -s tests -v` and fix failures
- [ ] T029 Verify coverage: `coverage run -m unittest discover -s tests && coverage report --fail-under=85` -> ensure ≥85%
- [ ] T030 Add integration smoke test: simulate a real bounce event and verify SMS fallback end-to-end (mock providers or test accounts)
- [ ] T031 Add docs: update `specs/001-outbound-communication/quickstart.md` with any required run steps discovered during implementation

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T032 [P] Add observability: metrics for attempted emails, SMS, bounce counts, latency exported via existing monitoring hooks
- [ ] T033 [P] Add retries and backoff policy tuning config options and document them in `.env.example` and `config.py`
- [ ] T034 [P] Security review: ensure secrets are read from env and not logged; update `.env.example` with placeholders
- [ ] T035 [P] Document operational runbook: who to contact on delivery outages and how to re-run failed communications

## Dependencies & Execution Order

- Phase 1 tasks (T001-T005) must complete before Phase 2
- Phase 2 tasks (T006-T012) must be written before implementation tasks in Phase 3
- Tools (T013-T015) and Types (T025) should be implemented before Node (T016-T022)
- Endpoint (T023-T024) is optional and can be implemented after Node and Tests pass

## Parallel Opportunities

- Tasks marked with `[P]` are parallelizable: T002, T003, T006-T009, T013-T015, T017-T019, T021, T024, T025, T032-T035
- Foundational tasks (T001-T005) are fast parallel tasks and can be assigned to different engineers

## Independent Test Criteria (per User Story)

- US1 (Email primary): Given a valid `recipient_email`, Mailchimp returns success -> final_status `delivered_email` and one `DeliveryAttempt` with provider `mailchimp` recorded.
- US2 (Email bounce -> SMS): Given a Mailchimp permanent bounce and `recipient_phone` present -> final_status `delivered_sms` and attempts recorded for both channels via same provider.
- US3 (Both fail): Email bounce and SMS failure -> final_status `failed` and human-review interrupt emitted with payload containing attempts and trace.

## Suggested MVP Scope

- MVP: Implement US1 (T013-T021 for tools and node) plus tests for email success (T006, T007) and basic QA (T026-T029). US2 (SMS fallback) is P1 feature but can be delivered in the next sprint if team size limited.

## Task Counts & Summary

- Total tasks: 35
- Tasks per story: US1 (core email): T013-T017, T025; US2 (SMS fallback): T018-T021; US3 (dual-failure handling): T022

---

Generated from: `specs/001-outbound-communication/spec.md`, `data-model.md`, `contracts/communication_api.md`
