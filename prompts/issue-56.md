## 1. Title and Overview

**Title:**
Implement Test Solver and Test Writer Agents with WorkflowMaster Integration

**Overview:**
This feature will introduce two specialized agents within the Gadugi agent ecosystem:
- **Test Solver Agent:** Autonomously analyzes and resolves failing tests, performing systematic failure analysis, resolution, and validation.
- **Test Writer Agent:** Authors new tests as required, ensuring proper coverage, documentation, and alignment with TDD practices.

Both agents will share a core operational framework covering test analysis, idempotency and dependency handling, resource management, and justification for any test skips. Additionally, the WorkflowMaster will be updated to detect contexts where these agents must be invoked, ensuring a robust, reliable, and maintainable testing strategy across the codebase.

**Context:**
Gadugi is now a mature, production-grade multi-agent platform with advanced orchestration, robust CI/CD, and comprehensive shared infrastructure. Testing quality and reliability are central to the platform’s ongoing maintainability and velocity. Automating intelligent test resolution and generation through these agents, orchestrated by WorkflowMaster, will further harden the system and accelerate future cycles.

---

## 2. Problem Statement

**Problem:**
Despite strong test coverage and advanced workflows, the process for addressing failing tests and expanding test coverage is still heavily manual. Failing tests can block merges or releases, and test authoring is inconsistent, leading to coverage gaps and incomplete documentation. There is no standardized, autonomous agent-based approach for systematically resolving or authoring tests in response to workflow needs.

**Current Limitations/Pain Points:**
- Failing tests require manual root cause analysis and remediation.
- Test writing is ad hoc; approaches and quality are inconsistent.
- Some failures are skipped without justification; some tests pass artificially or do not reflect real workflows.
- Resource leaks, idempotency issues, and poor dependency handling are missed in test routines.
- Development cycles are slowed by bottlenecks in failure triage and missing test coverage.

**Impact and Motivation:**
Without automated, principled handling for test failures and test authoring, development velocity, code quality, and release cadence suffer. This upgrade will allow WorkflowMaster to systematize test maintenance, enforce quality, and support TDD by having dedicated agents invoke standardized procedures for test failure recovery and new test creation.

---

## 3. Feature Requirements

**Functional Requirements:**
- Implement a **Test Solver Agent**:
    - Detect, analyze, and resolve failing tests via systematic process.
    - Provide a summary of root cause(s), remediation actions, and validation steps.
    - Only skip tests with explicit, well-justified and documented rationale.

- Implement a **Test Writer Agent**:
    - Author new tests as invoked by workflow, ensuring proper coverage, TDD alignment, and documentation.
    - Document intent and requirements for each test in code.
    - Use consistent fixtures, resource management, and dependency handling patterns.

- **Shared Instructions for Both Agents:**
    - Analyze the purpose, requirements, and expected outcome of each test/task.
    - Ensure idempotency and reliable resource management; prevent cross-test interference.
    - Use robust, reusable fixtures wherever possible.
    - Clean up any stateful resources after each test.
    - For skips: Only skip if a clear, documented reason exists (e.g., platform constraint, upstream bug).
    - Never introduce “artificial passes” or bypasses for unresolved failures.

- **WorkflowMaster Integration:**
    - Update WorkflowMaster to auto-invoke Test Solver for discovered failing tests.
    - Update WorkflowMaster to auto-invoke Test Writer when new code lacks coverage or when prompted by TDD/requirement analysis.

**Technical Requirements & Constraints:**
- Agents must be implemented as re-usable subagents following established agent patterns.
- Agents should be stateless per invocation; reuse project-wide fixtures for efficiency.
- Must operate autonomously but log all analysis, decisions, and actions.
- Integrate with existing Enhanced Separation, Container Execution, and TeamCoach systems.

**User Stories/Acceptance Criteria:**
1. As a maintainer, when a test fails, it should be automatically analyzed and (if possible) resolved by the Test Solver agent.
2. As a developer, when a new module/function is added, any coverage gaps should prompt the Test Writer agent to generate relevant tests.
3. All test passes and skips must be justified, documented, and leave the system in a clean state.
4. Agents should provide clear reports of actions taken, including what was analyzed, why, and how results were validated.

---

## 4. Technical Analysis

**Current Implementation Review:**
- No dedicated agents for automated test solving or test writing exist.
- Test maintenance is handled manually or ad hoc per PR.
- WorkflowMaster currently delegates to generic issue handlers for test failures.

**Proposed Technical Approach:**
- Define Test Solver and Test Writer as separate subagents in `.claude/agents/`.
- Agents share core logic for:
    - Purpose and requirements analysis
    - Idempotency and cleanup validation
    - Dependency handling and fixture use
- Distinct operational logic:
    - Solver: systematic analysis of failure, resolution strategies, skips only if justified, detailed remediation reporting.
    - Writer: analyzes uncovered code paths or TDD prompts and authors corresponding tests with full intent documentation.

**Architecture/Design Decisions:**
- Agents interact with the test discovery/execution tooling via Container Execution frameworks.
- All state and action reports piped through existing audit/logging channels.
- Agents can be invoked manually (developer request) or automatically (workflow triggers).

**Dependencies & Integration Points:**
- Enhanced Separation shared modules: for error handling, logging, test tracking.
- Container Execution Environment: secure test execution/isolation.
- TeamCoach: performance/status reporting.
- WorkflowMaster: agent orchestration & invocation.

**Performance Considerations:**
- Agents should minimize redundant runs (track previous attempts/retries).
- Prefer incremental test runs versus full suite when possible.
- Ensure no state leakage between repeated agent invocations.

---

## 5. Implementation Plan

**Phase 1: Agent Design & Core Logic**
- Define agent interfaces, core instruction sets, and shared helper functions.
- Implement logging, resource management, and fixture utilities.

**Phase 2: Solver Agent Implementation**
- Implement failure detection, analysis, resolution, skip justification, and reporting.

**Phase 3: Writer Agent Implementation**
- Implement test requirements discovery, test code generation, documentation embedding, and self-validation routines.

**Phase 4: WorkflowMaster Update**
- Update WorkflowMaster orchestration logic to invoke Test Solver/Writer at appropriate workflow junctures.
- Add new triggers for uncovered lines/branches and test failures.

**Phase 5: Testing/Validation**
- Write meta-tests to verify agent invocations, correctness, and reporting fidelity.
- Validate reliable fixture cleanup, resource idempotency, and agent statelessness.

**Deliverables:**
- Two agent modules, tests for agent logic, updated WorkflowMaster logic, demo/test cases, and documentation.

**Risk Assessment/Mitigation:**
- *Complex test failures with external dependencies:* Agents must gracefully skip with documentation if fix is outside current scope.
- *Resource leaks/idempotency bugs:* Core test runner updated to detect and log resource mismanagement.
- *Workflow integration errors:* Use thorough integration tests.

**Resources Required:**
- Access to agent registry, shared modules, testbed projects, and audit logging infrastructure.

---

## 6. Testing Requirements

**Unit Tests:**
- Coverage of all core shared instruction helpers, agent invocation, and analysis/reporting utilities.

**Integration Tests:**
- Test Solver properly receives failing test, produces valid resolution or justified skip, and logs evidence.
- Test Writer generates new tests, attaches documentation, and integrates with workflow as expected.

**Performance Testing:**
- Agent runs complete in reasonable time (<5 minutes for large projects).
- No increased resource leaks or test instability.

**Edge Cases & Error Scenarios:**
- Flaky tests: Solver retries, then skips with robust documentation if non-deterministic.
- Irreproducible/infrastructure failures: Clear reporting and deferment, not artificial pass.
- Test dependencies that require global state: Handled/isolated or explicitly skipped.

**Coverage Expectations:**
- All test pass scenarios, skips, and skips with justification are handled and reported.
- No orphaned or partial states after agent runs.

---

## 7. Success Criteria

**Measurable Outcomes:**
- >95% of failing tests are resolved or skipped with explicit, documented justification.
- 100% of newly added/modified code has corresponding test coverage authored by Test Writer.
- All tests are idempotent, reliable, and use shared fixtures or cleanup where possible.
- WorkflowMaster reliably invokes each agent per specification.
- Agents produce clear logs/reports for each run.

**Quality Metrics:**
- Test pass/failure rates before and after agent invocation.
- New code coverage percentages.
- Frequency/clarity of justified skips vs unjustified/excused failures.
- No lingering state/resources after runs.

**Performance Benchmarks:**
- Agent invocation time (median and 99th percentile).
- Time to resolution for failing tests.

**User Satisfaction Metrics:**
- Post-implementation developer survey (if available): efficacy, coverage, clarity.
- Reduction in manual triage/resolution for test failures.

---

## 8. Implementation Steps

1. **Issue Creation:**
   - Create/Update GitHub Issue with full description/requirements/acceptance criteria.
   - *Note: This issue was created by an AI agent on behalf of the repository owner.*

2. **Branch Management:**
   - Create feature branch: `feature/56-test-agents` from `main` following git guidelines.

3. **Research Phase:**
   - Analyze current test suite, discovery, and runner logic.
   - Locate agent registry and WorkflowMaster orchestration code.

4. **Agent Implementation:**
   - Implement Test Solver agent in `.claude/agents/test_solver_agent.py` (or interoperable path).
   - Implement Test Writer agent in `.claude/agents/test_writer_agent.py`.
   - Implement shared instruction/utils modules if needed.

5. **WorkflowMaster Modification:**
   - Update WorkflowMaster agent logic to:
      - Invoke Test Solver when failing test(s) detected at any CI/manual execution point.
      - Invoke Test Writer on new code with missing/flagged coverage.
      - Log all agent invocations/results to centralized audit trail.

6. **Testing and Validation:**
   - Write/execute agent unit tests.
   - Author meta-tests to confirm workflow orchestration logic.
   - Validate full cycle on testbed repo (major test failure, new code path, etc.).

7. **Documentation Updates:**
   - Add inline comments and update agent orchestration/change documentation.

8. **Pull Request Creation:**
   - Create PR from feature branch to main.
   - Title: `feat: Add Test Solver/Writer agents and integrate with WorkflowMaster`
   - Body: Detailed summary, test plan, agent descriptions, and
     "Note: This PR was created by an AI agent on behalf of the repository owner."

9. **Code Review:**
   - Invoke code-reviewer sub-agent for comprehensive review and validation.

---

**File Location:**
`/prompts/issue-56.md`

---

This prompt is ready for updating the associated issue and passing to the WorkflowMaster for complete workflow orchestration. It ensures clear, actionable, and testable steps, along with precise guidance and integration details.
