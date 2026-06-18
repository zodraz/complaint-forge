---

description: "Task list template for ComplaintForge feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for scenarios), research.md

**Tests**: MANDATORY - must achieve ≥85% code coverage per constitution. Tests written FIRST.

**Organization**: Tasks are grouped by feature type (Agent/Node/Tool) and user story, enabling independent implementation.

**Constitution Requirements**: All tasks must comply with:
1. **Code Quality**: Strict types, cyclomatic complexity ≤ 5, self-documenting code
2. **Testing**: TDD (tests first), ≥85% coverage, mock external services
3. **UX Consistency**: Empathetic tone, clear responses (for agents)
4. **Performance**: Latency SLAs, timeouts on external calls, state persistence

## Format: `[ID] [P?] [Type] Description`

- **[ID]**: Task identifier (T001, T002, etc.)
- **[P]**: Can run in parallel (independent files, no blocking dependencies)
- **[Type]**: Agent | Node | Tool | Test | Refactor
- Include exact file paths and dependencies in descriptions
- Mark dependency chain clearly (T010 blocks T011, T012, etc.)

## Phase 1: Setup & Test Infrastructure (FOUNDATIONAL)

**Purpose**: Establish testing framework and project structure

**⚠️ CRITICAL**: Complete before ANY feature implementation

- [ ] T001 Create test file: `tests/test_[feature].py` with imports and test class
- [ ] T002 [P] Add mocks for external services (Salesforce, Zendesk, A2A specialist)
- [ ] T003 [P] Setup test fixtures for complaint state and sample data
- [ ] T004 Configure coverage.py for ≥85% minimum enforcement
- [ ] T005 Validate .gitignore prevents `__pycache__` tracking

**Checkpoint**: Test infrastructure ready - write tests BEFORE implementation

---

## Phase 2: Tests for [Feature Name] (MANDATORY - Write FIRST)

**Purpose**: Define behavior via tests before implementing feature

> **TDD PROCESS**: Write tests → Verify FAIL → Implement → Verify PASS

### Unit Tests

- [ ] T006 [P] Test [function/method] with valid inputs in `tests/test_[feature].py`
- [ ] T007 [P] Test [function/method] error handling (edge cases, invalid inputs)
- [ ] T008 [P] Test [function/method] with mocked external service calls
- [ ] T009 [P] Test timeout/retry behavior for external service calls

### Integration Tests (if applicable)

- [ ] T010 Test end-to-end workflow integration (mock Salesforce, Zendesk, A2A)
- [ ] T011 Test state persistence through workflow nodes
- [ ] T012 Test escalation paths (policy → specialist_review → human_review)

**Checkpoint**: All tests written and verified FAILING before implementation proceeds

---

## Phase 3: Implementation - [Feature Type] (Priority: P1)

**Goal**: Implement [feature] meeting specification requirements and constitution standards

**Independent Test**: [How to verify this feature works independently]

### [IF AGENT] Agent Implementation

- [ ] T013 Create `agents/[name].py` with function signature and docstring
- [ ] T014 [P] Implement Azure OpenAI call via `llm_factory.get_chat_llm()`
- [ ] T015 [P] Set temperature to [0.0-1.0] with rationale in docstring
- [ ] T016 [P] Add input validation and output schema checking
- [ ] T017 Add error handling and logging for LLM calls
- [ ] T018 Verify ≥85% test coverage (run: `coverage report --fail-under=85`)
- [ ] T019 Run mypy strict type checking (run: `mypy --strict agents/[name].py`)

### [IF NODE] Node Implementation

- [ ] T013 Create `nodes/[name].py` with function signature and docstring
- [ ] T014 [P] Implement deterministic logic (no LLM calls except specialist_review)
- [ ] T015 [P] Add explicit error handling and recovery logic
- [ ] T016 [P] Set timeout for external service calls (Salesforce: 10s, A2A: 30s)
- [ ] T017 Add retry logic with exponential backoff
- [ ] T018 Implement state checkpointing after node completes
- [ ] T019 Verify ≥85% test coverage
- [ ] T020 Run mypy strict type checking

### [IF TOOL] Tool Implementation

- [ ] T013 Create `tools/[name]_tool.py` with function signatures
- [ ] T014 [P] Implement external service authentication (OAuth/token)
- [ ] T015 [P] Add timeout: [timeout_seconds] for all API calls
- [ ] T016 [P] Implement retry logic: exponential backoff, max [max_retries] attempts
- [ ] T017 [P] Add error handling: log and raise with context
- [ ] T018 Document config vars required in .env.example
- [ ] T019 Verify ≥85% test coverage with mocked external service
- [ ] T020 Run mypy strict type checking

### [IF ENDPOINT] API Endpoint Implementation

- [ ] T013 Create request/response Pydantic models in `main_fastapi.py`
- [ ] T014 Implement FastAPI route with 202 status for async operations
- [ ] T015 Add input validation via Pydantic
- [ ] T016 Implement thread_id tracking and state retrieval
- [ ] T017 Add error response handling (400, 404, 409, 500)
- [ ] T018 Verify ≥85% test coverage (test valid/invalid inputs, errors)
- [ ] T019 Run mypy strict type checking

**Checkpoint**: Feature fully implemented, all tests passing, coverage ≥85%

---

## Phase 4: Quality Assurance & Integration

- [ ] T021 Run linting: `ruff check agents/[name].py` → zero errors
- [ ] T022 Run type checking: `mypy --strict agents/[name].py` → zero errors
- [ ] T023 Run all tests: `python -B -m unittest discover -s tests -v` → all pass
- [ ] T024 Verify coverage: `coverage report --fail-under=85` → ≥85%
- [ ] T025 Code review: Minimum 1 approval from code owner
- [ ] T026 Integration test: Feature works with existing workflow (if applicable)

**Checkpoint**: Feature ready for merge and deployment

---

## Test Coverage by Feature Type

**Agents**: Mock LLM calls, validate outputs match expected schema, test error cases  
**Nodes**: Mock external services, test state transitions, validate routing logic  
**Tools**: Mock external service responses, test timeout/retry, validate error handling  
**Endpoints**: Mock graph calls, test valid/invalid inputs, test async state tracking  

**Run**: `python -B -m unittest discover -s tests -v`  
**Coverage**: `coverage run -m unittest discover -s tests && coverage report --fail-under=85`

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T021 [US2] Implement [Service] in src/services/[service].py
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T027 [US3] Implement [Service] in src/services/[service].py
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
