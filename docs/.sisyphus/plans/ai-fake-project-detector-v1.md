# AI Fake Project Detector V1 Work Plan

## TL;DR

> **Quick Summary**: Deliver a GitHub-first, explainable AI project evaluation product that analyzes repositories, compares them against peers, produces evidence-backed risk reports, supports ranking/search/history, and provides lightweight authenticated feedback without letting feedback directly drive the core score.
>
> **Deliverables**:
> - Updated authoritative planning artifacts and synced project docs scope
> - Stable analysis pipeline: ingestion → structure → peer baseline → explainable scoring
> - Persisted analysis history, ranking/search views, and repo detail experience
> - Authenticated lightweight feedback with anti-abuse guardrails
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 6 waves + final verification
> **Critical Path**: Task 5 → Task 8 → Task 11 → Task 12 → Task 13 → Final Verification

---

## Context

### Original Request
Rework the current project PRD, clarify requirements, ensure strong product competitiveness, plan development tasks, derive executable steps, and then hand execution to Sisyphus.

### Interview Summary
**Key Discussions**:
- Product wedge is **explainable scoring + peer comparison**, not generic discovery.
- Delivery should be dual-track: authoritative plan under `.sisyphus/`, with mapping for how `docs/*.md` should be updated.
- V1 must include: single-repo analysis, peer comparison, explainable report, ranking over analyzed repos, search/filter, score history, and lightweight authenticated feedback.
- Test strategy is **TDD**.
- Voting/feedback must be separated from core score and treated as a credibility layer, not as ranking authority.

**Research Findings**:
- Existing docs align on a GitHub-first fake-risk analysis concept, but current `docs/PLAN.md` and `docs/TODO.md` are too coarse for execution.
- Oracle guidance: the most credible MVP is GitHub-only analysis plus peer-relative explainable scoring; X/Twitter must stay deferred.
- Competitor research: discovery feeds, repo analytics, and security tools are siloed; the whitespace is a cross-signal verdict engine answering whether a hot AI OSS repo is substantive or narrative-heavy.
- Existing codebase already contains working modules and tests for repo ingestion, structure analysis, peer retrieval, scoring, plus Flask/Streamlit demo surfaces.

### Metis Review
**Identified Gaps** (Metis consultation timed out, so these were carried forward from prior analysis and self-review):
- Explicit guardrails are needed around terminology, peer comparability, feedback influence, and UI surface consolidation.
- Scope creep risk is high around X/Twitter ingestion, embeddings-first retrieval, and social/community features.
- Acceptance criteria must define report completeness, ranking behavior, history persistence, and anti-abuse constraints.

---

## Work Objectives

### Core Objective
Ship a production-shaped V1 that can analyze a GitHub repository, explain its risk using concrete evidence and peer-normalized context, retain history for re-analysis, and let users explore analyzed projects through searchable ranking/detail experiences.

### Concrete Deliverables
- `docs/PRD.md`, `docs/SOLUTION.md`, `docs/PLAN.md`, `docs/TODO.md` synced to the clarified V1 scope
- Stable analysis pipeline across `modules/repo_ingestion`, `modules/structure_analyzer`, `modules/peer_retrieval`, `modules/scoring_engine`
- Persistence layer for analyzed repos, report snapshots, ranking views, feedback records, and history
- Flask-based web application and JSON endpoints for analysis, detail, ranking, search/filter, history, and authenticated feedback
- Test suite covering TDD module behavior, integration flow, and end-user report/ranking interactions

### Definition of Done
- [ ] A valid GitHub URL can be analyzed end-to-end and stored as a versioned report snapshot
- [ ] Result pages expose total score, dimension breakdown, evidence cards, guardrail notes, peer baseline summary, and history entries
- [ ] Ranking/search pages list analyzed repos only and support filters/sorting defined in PRD
- [ ] Authenticated feedback is stored, de-duplicated, rate-limited, displayed separately from the core score, and does not directly overwrite risk scoring
- [ ] All targeted tests pass and final QA evidence exists under `.sisyphus/evidence/`

### Must Have
- Explainable scoring: every notable score outcome must map to visible evidence
- Peer-normalized comparison with rule-first comparability guardrails
- GitHub-only V1 with no hard dependency on X/Twitter APIs
- TDD workflow for implementation tasks
- Search/filter and score history included in V1

### Must NOT Have (Guardrails)
- No black-box end-to-end scoring model in V1
- No anonymous voting or feedback directly affecting rank/score authority
- No universal “all GitHub projects” leaderboard; rankings are over analyzed repos only
- No X/Twitter ingestion dependency on the critical path
- No “fraud/scam” wording in user-facing language; use risk/credibility/verification phrasing
- No maintaining two primary product surfaces; one primary web surface must be chosen and demos downgraded or aligned

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — all verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (pytest-based tests already present)
- **Automated tests**: TDD
- **Framework**: pytest
- **If TDD**: each task follows RED → GREEN → REFACTOR

### QA Policy
Every task includes agent-executed QA scenarios with evidence captured in `.sisyphus/evidence/`.

- **Frontend/UI**: Browser automation against the primary web app
- **API/Backend**: HTTP requests against JSON endpoints
- **Library/Module**: pytest-targeted unit/integration tests and small runtime checks
- **CLI/TUI**: only if a local runner or debug script is part of the task

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation):
├── Task 1: Sync product docs and V1 guardrails [writing]
├── Task 2: Consolidate module contracts and scoring semantics [deep]
├── Task 3: Create labeled fixtures + peer baseline dataset [quick]
├── Task 4: Decide and align primary app surface [unspecified-high]
└── Task 5: Introduce persistence schema for analyses/history/feedback [unspecified-high]

Wave 2 (Core logic in parallel):
├── Task 6: Harden peer retrieval with rule-first fallback [deep]
└── Task 7: Rebuild explainable scoring engine outputs [deep]

Wave 3 (Analysis orchestration):
└── Task 8: Build analysis orchestration + snapshot persistence [unspecified-high]

Wave 4 (Read surfaces + feedback):
├── Task 9: Build repo detail/history API + page [visual-engineering]
├── Task 10: Build analyzed-repo ranking/search/filter experience [visual-engineering]
└── Task 11: Add authenticated lightweight feedback + anti-abuse [unspecified-high]

Wave 5 (Cross-surface integration):
└── Task 12: Integrate ranking/detail/report surfaces end-to-end [deep]

Wave 6 (Coverage + docs sync):
├── Task 13: Add regression/integration/E2E coverage for v1 flows [unspecified-high]
└── Task 14: Sync project docs/TODO to shipped behavior [writing]

Wave FINAL:
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real QA execution (unspecified-high)
└── Task F4: Scope fidelity check (deep)
```

### Dependency Matrix

- **1**: — → 14
- **2**: — → 6, 7, 8
- **3**: — → 6, 7, 13
- **4**: — → 9, 10, 12
- **5**: — → 8, 9, 10, 11, 12
- **6**: 2, 3 → 8, 13
- **7**: 2, 3 → 8, 9, 10, 12, 13
- **8**: 2, 5, 6, 7 → 9, 10, 11, 12, 13
- **9**: 4, 5, 7, 8 → 12, 13
- **10**: 4, 5, 7, 8 → 12, 13
- **11**: 5, 8 → 12, 13
- **12**: 8, 9, 10, 11 → 13, 14
- **13**: 3, 6, 7, 8, 9, 10, 11, 12 → FINAL
- **14**: 1, 12 → FINAL

### Agent Dispatch Summary

- **Wave 1**: T1 → `writing`, T2 → `deep`, T3 → `quick`, T4 → `unspecified-high`, T5 → `unspecified-high`
- **Wave 2**: T6 → `deep`, T7 → `deep`
- **Wave 3**: T8 → `unspecified-high`
- **Wave 4**: T9 → `visual-engineering`, T10 → `visual-engineering`, T11 → `unspecified-high`
- **Wave 5**: T12 → `deep`
- **Wave 6**: T13 → `unspecified-high`, T14 → `writing`
- **Final**: F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Sync product docs and V1 guardrails

  **What to do**:
  - Rewrite project-facing docs so `docs/PRD.md`, `docs/SOLUTION.md`, `docs/PLAN.md`, and `docs/TODO.md` all express the same V1 contract: GitHub-first, explainable scoring, peer comparison, analyzed-repo ranking, search/filter, score history, and authenticated lightweight feedback.
  - Normalize user-facing terminology away from accusatory wording toward verification/risk language.
  - Make deferred scope explicit: X/Twitter ingestion, anonymous voting, public API, appeals, comments, advanced fraud detection.

  **Must NOT do**:
  - Do not introduce features in docs that are intentionally deferred.
  - Do not describe feedback as a direct input to final risk score.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: this task is document-contract alignment and terminology control.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no UI behavior is changed here.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 14
  - **Blocked By**: None

  **References**:
  - `projects/ai-fake-project-detector/docs/PRD.md` - current product scope and rubric language to replace/clarify
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - current architecture assumptions to keep aligned with PRD
  - `projects/ai-fake-project-detector/docs/PLAN.md` - current milestone structure that needs conversion into executable slices
  - `projects/ai-fake-project-detector/docs/TODO.md` - current backlog seed that should become implementation-facing
  - `projects/ai-fake-project-detector/memory/INDEX.md` - existing project decisions about explainability, GitHub-first scope, and ranking strategy

  **Acceptance Criteria**:
  - [ ] All four docs describe the same V1 feature set and same explicit deferred items
  - [ ] PRD terminology no longer uses escalatory scam/fraud wording in user-facing descriptions
  - [ ] PLAN and TODO reflect TDD and analyzed-repo-only ranking scope

  **QA Scenarios**:
  ```
  Scenario: Doc contract alignment
    Tool: Bash (python or diff-capable check) + Read
    Preconditions: Updated docs exist
    Steps:
      1. Read PRD/SOLUTION/PLAN/TODO and compare feature lists for V1 + deferred scope.
      2. Assert all mention GitHub-first, search/filter, score history, and authenticated feedback.
      3. Assert none describe X/Twitter as MVP-critical or feedback as direct score authority.
    Expected Result: Cross-doc contract is consistent with no scope contradictions.
    Failure Indicators: Missing feature in one doc, conflicting scope, or terminology drift.
    Evidence: .sisyphus/evidence/task-1-doc-contract.txt

  Scenario: Terminology guardrail
    Tool: Grep
    Preconditions: Docs updated
    Steps:
      1. Search docs for forbidden terms like `scam`, `fraud`, `fake project` in accusatory presentation contexts.
      2. Verify approved alternatives such as `risk`, `credibility`, `verification`, `substance` are used.
    Expected Result: No forbidden escalatory wording remains in user-facing product docs.
    Evidence: .sisyphus/evidence/task-1-terminology.txt
  ```

- [x] 2. Consolidate module contracts and scoring semantics

  **What to do**:
  - Update module SPECs and implementation-facing contracts so repo ingestion, structure analysis, peer retrieval, and scoring use consistent shapes, naming, and score semantics.
  - Resolve the current ambiguity where dimension sub-scores sometimes read as “goodness” while total score is “risk”.
  - Define peer-baseline fallback behavior and history snapshot schema expectations.

  **Must NOT do**:
  - Do not leave contradictory risk-level mappings between PRD, SPECs, and tests.
  - Do not require embedding-only retrieval for V1.

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: this task touches contract semantics across multiple modules and tests.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `writing`: docs alone are insufficient; implementation contracts must be aligned.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 6, 7, 8
  - **Blocked By**: None

  **References**:
  - `projects/ai-fake-project-detector/modules/repo-ingestion/SPEC.md` - ingestion output contract
  - `projects/ai-fake-project-detector/modules/structure-analyzer/SPEC.md` - structure feature contract
  - `projects/ai-fake-project-detector/modules/peer-retrieval/SPEC.md` - peer retrieval API and strategy definitions
  - `projects/ai-fake-project-detector/modules/scoring-engine/SPEC.md` - scoring semantics and current rubric drift
  - `projects/ai-fake-project-detector/memory/sessions/2026-03-30_16-01.md` - previous contract-fix session and remaining peer/scoring drift
  - `projects/ai-fake-project-detector/tests/test_peer_retrieval.py` - current tested retrieval assumptions
  - `projects/ai-fake-project-detector/tests/test_scoring_engine.py` - current tested score assumptions

  **Acceptance Criteria**:
  - [ ] All relevant SPECs define compatible field names and score semantics
  - [ ] Risk-level thresholds are identical across PRD, SPECs, and tests
  - [ ] Peer-retrieval strategy definition explicitly supports rule-first fallback for V1

  **QA Scenarios**:
  ```
  Scenario: Contract consistency review
    Tool: Read + Grep
    Preconditions: SPECs and tests updated
    Steps:
      1. Read all four module SPECs and grep for key fields (`fake_risk_score`, `risk_level`, `similarity_score`, `file_tree`).
      2. Compare field semantics and threshold mapping across docs/tests.
      3. Assert no contradictory descriptions remain.
    Expected Result: Contracts are mutually consistent and executable.
    Evidence: .sisyphus/evidence/task-2-contract-consistency.txt

  Scenario: Negative drift detection
    Tool: Grep
    Preconditions: Updated files exist
    Steps:
      1. Search for conflicting risk band text and contradictory comments like `high score means good delivery` alongside total risk semantics.
      2. Verify conflicts were removed or normalized.
    Expected Result: No contradictory score semantics remain.
    Evidence: .sisyphus/evidence/task-2-risk-drift.txt
  ```

- [x] 3. Create labeled fixtures and peer baseline dataset

  **What to do**:
  - Build a small deterministic fixture set representing at least three cohorts: clearly substantive, clearly hype-heavy, and early-but-real projects.
  - Define fields needed for peer baseline generation, score regression tests, and history snapshots.
  - Ensure fixtures are reusable by retrieval, scoring, ranking, and history tests.

  **Must NOT do**:
  - Do not depend on live third-party APIs for baseline tests.
  - Do not create unlabeled fixtures with no expected score/risk intent.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: bounded data/test-fixture work with high leverage across later tasks.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `deep`: the task is structured data prep rather than complex architecture.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 6, 7, 13
  - **Blocked By**: None

  **References**:
  - `projects/ai-fake-project-detector/tests/test_peer_retrieval.py` - current candidate/target shape for retrieval fixtures
  - `projects/ai-fake-project-detector/tests/test_scoring_engine.py` - current scoring fixture expectations
  - `projects/ai-fake-project-detector/docs/PRD.md` - rubric and protection rules to encode in sample cohorts
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - peer baseline and guardrail concepts the fixtures must support

  **Acceptance Criteria**:
  - [ ] Fixture set includes labeled repos for substantive, hype-heavy, and early-but-real cases
  - [ ] Tests can use fixtures without network access
  - [ ] Expected cohort intent is documented and assertable in tests

  **QA Scenarios**:
  ```
  Scenario: Fixture cohort coverage
    Tool: Read
    Preconditions: Fixture files/test helpers created
    Steps:
      1. Read fixture definitions.
      2. Verify presence of at least one sample per required cohort.
      3. Verify each sample carries enough fields for retrieval/scoring/history tests.
    Expected Result: Deterministic labeled fixture coverage is complete.
    Evidence: .sisyphus/evidence/task-3-fixtures.txt

  Scenario: Offline test safety
    Tool: Grep
    Preconditions: Tests updated to use fixtures
    Steps:
      1. Search fixture-driven tests for live GitHub/network calls.
      2. Confirm retrieval/scoring regression tests can run offline.
    Expected Result: No network dependency remains in baseline/regression fixtures.
    Evidence: .sisyphus/evidence/task-3-offline-safety.txt
  ```

- [x] 4. Decide and align primary app surface

  **What to do**:
  - Select one primary product surface for V1 (Flask web app + JSON API is the likely canonical path given templates and routing).
  - Align or downgrade alternative demo surfaces so there is no conflicting primary UX or duplicate business logic.
  - Define how template pages, APIs, and any demo app should coexist without divergence.

  **Must NOT do**:
  - Do not maintain both Flask and Streamlit as equal first-class V1 surfaces.
  - Do not keep mock/demo-only data paths in the primary runtime path.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: requires product/runtime consolidation across app surfaces.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `visual-engineering`: this is architecture/surface consolidation first.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 9, 10, 12
  - **Blocked By**: None

  **References**:
  - `projects/ai-fake-project-detector/flask_app.py` - strongest current app shell with templates and JSON endpoint
  - `projects/ai-fake-project-detector/streamlit_app.py` - alternate surface currently duplicating orchestration logic
  - `projects/ai-fake-project-detector/simple_app.py` - mock/demo-only fallback path that should not remain primary
  - `projects/ai-fake-project-detector/templates/index.html` - existing landing/input flow
  - `projects/ai-fake-project-detector/templates/results.html` - existing result rendering flow

  **Acceptance Criteria**:
  - [ ] One primary app surface is documented and wired as canonical V1 path
  - [ ] Demo/mock paths are either removed from primary flow or clearly isolated
  - [ ] No duplicated orchestration logic remains across competing surfaces

  **QA Scenarios**:
  ```
  Scenario: Primary surface determination
    Tool: Read
    Preconditions: App entrypoints updated
    Steps:
      1. Read app entrypoint files and docs.
      2. Verify only one runtime path is documented as V1 primary surface.
      3. Confirm alternatives are marked demo/dev-only or aligned to shared services.
    Expected Result: Product surface ownership is unambiguous.
    Evidence: .sisyphus/evidence/task-4-primary-surface.txt

  Scenario: Mock path exclusion
    Tool: Grep
    Preconditions: Primary runtime path updated
    Steps:
      1. Search primary app files for hardcoded `MOCK_` data and fallback import stubs.
      2. Verify mock behavior is not part of the production route path.
    Expected Result: Primary V1 flow no longer depends on demo-only mocks.
    Evidence: .sisyphus/evidence/task-4-mock-exclusion.txt
  ```

- [x] 5. Introduce persistence schema for analyses, history, and feedback

  **What to do**:
  - Add a persistence layer for analyzed repositories, report snapshots, ranking materialization inputs, feedback records, and score-history retrieval.
  - Define versioned snapshot storage so re-analysis creates history instead of overwriting prior evidence.
  - Establish data contracts for ranking/search queries and authenticated feedback deduplication.

  **Must NOT do**:
  - Do not keep history only in memory.
  - Do not design feedback storage that can overwrite core scoring facts.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: persistence design impacts ranking, history, and feedback integration.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `quick`: too many downstream contracts depend on this schema work.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 8, 9, 10, 11, 12
  - **Blocked By**: None

  **References**:
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - required product capabilities for ranking, voting, and detail views
  - `projects/ai-fake-project-detector/docs/PRD.md` - score history, ranking, and voting expectations
  - `projects/ai-fake-project-detector/flask_app.py` - current runtime has no persisted snapshots and needs orchestration target shape

  **Acceptance Criteria**:
  - [ ] Re-analysis creates a new report snapshot linked to the same repo identity
  - [ ] Ranking/search can query analyzed repos without recomputing every request
  - [ ] Feedback records include auth identity, project identity, timestamp, and dedupe fields

  **QA Scenarios**:
  ```
  Scenario: Snapshot versioning
    Tool: Bash (pytest or runtime check)
    Preconditions: Persistence layer implemented with tests
    Steps:
      1. Create an analyzed repo record and persist one report snapshot.
      2. Persist a second analysis for the same repo.
      3. Assert history returns two ordered snapshots without deleting the first.
    Expected Result: History is append-only and versioned.
    Evidence: .sisyphus/evidence/task-5-history-versioning.txt

  Scenario: Feedback dedupe fields
    Tool: Read + Bash (pytest)
    Preconditions: Feedback storage model implemented
    Steps:
      1. Inspect schema/tests for identity + repo + time-based dedupe fields.
      2. Submit duplicate feedback in test code.
      3. Assert only one effective record is counted per dedupe window.
    Expected Result: Feedback storage supports anti-abuse constraints.
    Evidence: .sisyphus/evidence/task-5-feedback-dedupe.txt
  ```

- [x] 6. Harden peer retrieval with rule-first fallback

  **What to do**:
  - Implement V1 retrieval as rule-first comparability, using deterministic category/feature matching before any optional hybrid similarity.
  - Provide fallback behavior when too few comparable peers exist.
  - Produce machine-readable peer comparison outputs used by scoring, detail pages, and ranking explanations.

  **Must NOT do**:
  - Do not make embeddings mandatory in V1.
  - Do not compare repos across obviously mismatched categories without an explicit low-confidence flag.

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: retrieval quality is core to credibility and depends on contract + dataset design.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `quick`: retrieval fallback and confidence behavior require deeper reasoning.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 7, 8, 13
  - **Blocked By**: 2, 3

  **References**:
  - `projects/ai-fake-project-detector/modules/peer-retrieval/SPEC.md` - current strategy surface and fallback ambiguity
  - `projects/ai-fake-project-detector/modules/peer_retrieval/peer_retrieval.py` - existing retrieval implementation to evolve
  - `projects/ai-fake-project-detector/tests/test_peer_retrieval.py` - current expectations and regression starting point
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - recommendation to use rules + similarity hybrid with cold-start safety
  - `projects/ai-fake-project-detector/docs/PRD.md` - comparability is essential to user trust

  **Acceptance Criteria**:
  - [ ] Retrieval returns comparable peers with similarity/confidence metadata
  - [ ] Low-peer-count cases return deterministic fallback behavior plus disclosure
  - [ ] Retrieval tests cover same-category, mismatched-category, and insufficient-peer paths

  **QA Scenarios**:
  ```
  Scenario: Comparable peer retrieval
    Tool: Bash (pytest)
    Preconditions: Retrieval tests and fixtures implemented
    Steps:
      1. Run retrieval against a substantive Python-target fixture.
      2. Assert top peers come from the intended comparable cohort.
      3. Assert each result includes similarity score and explanation/confidence data.
    Expected Result: Retrieval is deterministic and peer-normalized.
    Evidence: .sisyphus/evidence/task-6-peer-retrieval.txt

  Scenario: Insufficient peer fallback
    Tool: Bash (pytest)
    Preconditions: Sparse-peer fixture exists
    Steps:
      1. Run retrieval for a repo with too few comparable candidates.
      2. Assert fallback behavior is triggered.
      3. Assert downstream metadata clearly marks low-confidence comparison.
    Expected Result: Sparse datasets degrade gracefully instead of producing misleading peers.
    Evidence: .sisyphus/evidence/task-6-peer-fallback.txt
  ```

- [x] 7. Rebuild explainable scoring engine outputs

  **What to do**:
  - Align scoring implementation with the clarified rubric so total score is a risk score and all dimensions contribute coherently.
  - Generate evidence cards, guardrail notes, peer baseline summaries, and low-confidence disclosures.
  - Ensure early-but-real fixture cases benefit from protection rules instead of being over-penalized.

  **Must NOT do**:
  - Do not let feedback directly rewrite total risk score in V1.
  - Do not emit a total score without at least the minimum evidence/guardrail payload.

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: this is the core moat and requires careful logic plus protective exceptions.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `writing`: explanation text matters, but the hard part is scoring semantics and evidence generation.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 8, 9, 10, 12, 13
  - **Blocked By**: 2, 3

  **References**:
  - `projects/ai-fake-project-detector/modules/scoring-engine/SPEC.md` - current rubric mapping and semantic drift
  - `projects/ai-fake-project-detector/modules/scoring_engine/scoring_engine.py` - existing implementation to align
  - `projects/ai-fake-project-detector/tests/test_scoring_engine.py` - current score behavior and regression harness
  - `projects/ai-fake-project-detector/docs/PRD.md` - official rubric, risk bands, and protection rules
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - expected scoring outputs and guardrail intent

  **Acceptance Criteria**:
  - [ ] Total risk score and risk levels match the PRD rubric
  - [ ] Each report contains at least 3 evidence cards and 1 guardrail/disclaimer note
  - [ ] Early-but-real fixtures avoid false extreme-risk classification via protection rules

  **QA Scenarios**:
  ```
  Scenario: Risk semantics regression
    Tool: Bash (pytest)
    Preconditions: Updated scoring tests exist
    Steps:
      1. Run scoring tests for substantive, hype-heavy, and early-but-real fixtures.
      2. Assert risk ordering matches cohort intent.
      3. Assert risk-level labels match PRD thresholds.
    Expected Result: Scoring is rubric-aligned and stable.
    Evidence: .sisyphus/evidence/task-7-risk-regression.txt

  Scenario: Missing evidence payload failure
    Tool: Bash (pytest)
    Preconditions: Negative test exists
    Steps:
      1. Trigger scoring for a repo case that would previously omit evidence cards or guardrail notes.
      2. Assert output still contains required explainability payload.
    Expected Result: Reports cannot be emitted without required evidence metadata.
    Evidence: .sisyphus/evidence/task-7-evidence-minimum.txt
  ```

- [x] 8. Build analysis orchestration and snapshot persistence

  **What to do**:
  - Create the end-to-end orchestration path that fetches repo data, analyzes structure, retrieves peers, computes score, and persists a report snapshot.
  - Remove hardcoded peer/vote placeholders from the primary flow.
  - Expose a stable service/API contract for analysis requests and re-analysis.

  **Must NOT do**:
  - Do not leave mock baseline/voting dictionaries in the primary analysis path.
  - Do not compute ranking/history off transient in-memory results only.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: orchestration spans multiple modules, persistence, and runtime entrypoints.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `quick`: too much cross-module integration for a simple category.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 9, 10, 11, 12, 13
  - **Blocked By**: 2, 5, 6, 7

  **References**:
  - `projects/ai-fake-project-detector/flask_app.py` - current orchestration path with hardcoded baseline and feedback placeholders
  - `projects/ai-fake-project-detector/streamlit_app.py` - duplicated orchestration logic to consolidate or downgrade
  - `projects/ai-fake-project-detector/modules/repo_ingestion/repo_ingestion.py` - ingestion runtime input
  - `projects/ai-fake-project-detector/modules/structure_analyzer/structure_analyzer.py` - structure analysis runtime input
  - `projects/ai-fake-project-detector/modules/peer_retrieval/peer_retrieval.py` - peer baseline source
  - `projects/ai-fake-project-detector/modules/scoring_engine/scoring_engine.py` - final report source

  **Acceptance Criteria**:
  - [ ] Primary analysis route persists a snapshot instead of returning ephemeral-only data
  - [ ] Re-analysis creates a new versioned snapshot linked to the same repo
  - [ ] No hardcoded mock baseline or mock feedback values remain in primary path

  **QA Scenarios**:
  ```
  Scenario: End-to-end analysis snapshot
    Tool: Bash (pytest or HTTP client)
    Preconditions: Primary app or service running with persistence enabled
    Steps:
      1. Submit a valid GitHub repo URL to the analysis endpoint.
      2. Assert response includes report payload and stored snapshot identifier.
      3. Query history for the same repo and confirm the snapshot appears.
    Expected Result: Analysis flow is persisted and replayable.
    Evidence: .sisyphus/evidence/task-8-analysis-snapshot.txt

  Scenario: Placeholder removal
    Tool: Grep
    Preconditions: Primary analysis path updated
    Steps:
      1. Search primary runtime files for hardcoded peer baseline and zeroed voting dictionaries.
      2. Verify primary path now resolves these via services/persistence.
    Expected Result: Production path no longer depends on static placeholders.
    Evidence: .sisyphus/evidence/task-8-placeholder-removal.txt
  ```

- [x] 9. Build repo detail and score-history experience

  **What to do**:
  - Create repo detail endpoints/pages showing latest score, evidence, guardrail notes, peer summary, and chronological score history.
  - Ensure users can inspect how a repo changed between analyses without losing prior evidence context.
  - Surface low-confidence peer comparison and disclaimer messaging on the detail experience.

  **Must NOT do**:
  - Do not show only the latest snapshot when history exists.
  - Do not hide disclaimers or guardrail notes on the detail page.

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: page/API assembly with clear evidence presentation and history UX.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `writing`: UX rendering and data wiring dominate this task.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 12, 13
  - **Blocked By**: 4, 5, 7, 8

  **References**:
  - `projects/ai-fake-project-detector/templates/results.html` - current result page that lacks persisted history and peer-confidence UX
  - `projects/ai-fake-project-detector/flask_app.py` - current result rendering and JSON response path
  - `projects/ai-fake-project-detector/docs/PRD.md` - history requirement and report completeness requirements
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - expected report output shape

  **Acceptance Criteria**:
  - [ ] Detail experience shows latest report plus chronological score history
  - [ ] Detail experience includes evidence cards, peer summary, and guardrail/disclaimer content
  - [ ] History view distinguishes snapshots by timestamp/version

  **QA Scenarios**:
  ```
  Scenario: Repo detail happy path
    Tool: Playwright or browser-capable UI automation
    Preconditions: Primary web app running with at least one analyzed repo with history
    Steps:
      1. Open the repo detail page.
      2. Assert the page shows total score, risk label, at least 3 evidence cards, and guardrail notes.
      3. Assert a history section lists multiple snapshot timestamps.
    Expected Result: Detail page exposes the full explainability payload plus history.
    Evidence: .sisyphus/evidence/task-9-detail-page.png

  Scenario: No-history / single-history edge case
    Tool: Playwright or browser-capable UI automation
    Preconditions: Repo exists with only one snapshot
    Steps:
      1. Open detail page for a single-snapshot repo.
      2. Assert the history module renders a graceful empty/minimal state rather than failing.
    Expected Result: History UI handles single-snapshot repos cleanly.
    Evidence: .sisyphus/evidence/task-9-history-edge.png
  ```

- [x] 10. Build analyzed-repo ranking, search, and filter experience

  **What to do**:
  - Build ranking endpoints/pages over analyzed repos only.
  - Add search and filter controls aligned with V1 PRD (e.g., language/category/risk band/update time as applicable to actual data model).
  - Make ranking logic transparent and separate from lightweight feedback authority.

  **Must NOT do**:
  - Do not present rankings as a universal GitHub leaderboard.
  - Do not reorder ranking directly from raw feedback counts.

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: requires browse UX, filters, and ranking transparency.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `deep`: ranking logic matters, but the primary workload is browse experience + query wiring.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 12, 13
  - **Blocked By**: 4, 5, 7, 8

  **References**:
  - `projects/ai-fake-project-detector/docs/PRD.md` - ranking page requirement, search/tag/category requirement
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - ranking-service expectations
  - `projects/ai-fake-project-detector/flask_app.py` - current app routes that need browse/list expansion
  - `projects/ai-fake-project-detector/templates/index.html` - current entry page and styling baseline

  **Acceptance Criteria**:
  - [ ] Ranking page lists analyzed repos only with score, risk label, vote/feedback summary, and updated time
  - [ ] Search/filter interactions return deterministic subsets with no server errors
  - [ ] Ranking explanation text discloses main ordering basis and that feedback is supplemental only

  **QA Scenarios**:
  ```
  Scenario: Ranking browse and filter
    Tool: Playwright or browser-capable UI automation
    Preconditions: App seeded with multiple analyzed repos
    Steps:
      1. Open ranking page.
      2. Apply a specific filter such as risk band or language.
      3. Assert the list updates and every visible row satisfies the selected filter.
    Expected Result: Ranking search/filter works on analyzed repos only.
    Evidence: .sisyphus/evidence/task-10-ranking-filter.png

  Scenario: Ranking authority guardrail
    Tool: Read + Playwright
    Preconditions: Ranking page implemented
    Steps:
      1. Inspect page copy and row metadata.
      2. Assert ordering basis/disclaimer is visible.
      3. Confirm feedback counts are displayed as supplemental signal, not as the main sort claim.
    Expected Result: Ranking transparency guardrail is visible to users.
    Evidence: .sisyphus/evidence/task-10-ranking-guardrail.txt
  ```

- [x] 11. Add authenticated lightweight feedback and anti-abuse controls

  **What to do**:
  - Implement login-gated feedback actions such as agree / disagree / needs-review (or equivalent approved lightweight set).
  - Add deduplication, rate limiting, anomaly flags, and storage/display rules.
  - Keep feedback presentation separate from authoritative risk score generation and ranking basis.

  **Must NOT do**:
  - Do not add anonymous feedback for V1.
  - Do not let feedback actions rewrite score snapshots directly.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: combines auth, storage, anti-abuse, and product-governance concerns.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `visual-engineering`: governance and state/control logic are the primary challenge.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: 12, 13
  - **Blocked By**: 5, 8

  **References**:
  - `projects/ai-fake-project-detector/docs/PRD.md` - voting/feedback requirement and anti-brush expectations
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - voting-service and governance guidance
  - `projects/ai-fake-project-detector/flask_app.py` - current runtime lacks auth/feedback endpoints and must remain separate from score authority

  **Acceptance Criteria**:
  - [ ] Only authenticated users can submit feedback
  - [ ] Duplicate submissions within the configured window are rejected or collapsed
  - [ ] Feedback summary is displayed separately from the risk score and marked supplemental

  **QA Scenarios**:
  ```
  Scenario: Authenticated feedback happy path
    Tool: Playwright + HTTP assertions if needed
    Preconditions: App running with auth and at least one analyzed repo
    Steps:
      1. Sign in as a test user.
      2. Open a repo detail page and submit one feedback action.
      3. Assert the feedback summary updates and the risk score itself does not change instantly.
    Expected Result: Feedback is accepted, persisted, and separated from core score display.
    Evidence: .sisyphus/evidence/task-11-feedback-happy.png

  Scenario: Duplicate/rate-limit rejection
    Tool: Playwright or Bash (HTTP)
    Preconditions: Same signed-in user/session
    Steps:
      1. Submit the same feedback again within the dedupe window.
      2. Assert the second action is blocked or collapsed according to spec.
      3. Verify anomaly/rate-limit metadata is recorded if applicable.
    Expected Result: Anti-abuse controls work without crashing the page.
    Evidence: .sisyphus/evidence/task-11-feedback-reject.txt
  ```

- [x] 12. Integrate ranking, detail, and report surfaces end-to-end

  **What to do**:
  - Wire the primary app so users can move from submission → report → repo detail/history → ranking/search and back.
  - Ensure shared rendering/components use one canonical source of truth for score cards, evidence cards, disclaimers, and repo metadata.
  - Remove remaining route-level duplication and align JSON/API outputs with UI expectations.

  **Must NOT do**:
  - Do not keep separate incompatible payload shapes between API and page rendering for the same concept.
  - Do not leave dead routes pointing to stale demo behavior.

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: this is the cross-surface integration point with multiple dependencies.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `visual-engineering`: integration/contract coherence is broader than page styling.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: 13, 14
  - **Blocked By**: 8, 9, 10, 11

  **References**:
  - `projects/ai-fake-project-detector/flask_app.py` - central route integration target
  - `projects/ai-fake-project-detector/templates/index.html` - submission path baseline
  - `projects/ai-fake-project-detector/templates/results.html` - current report rendering baseline
  - `projects/ai-fake-project-detector/docs/PLAN.md` - earlier milestone expectations that this task operationalizes

  **Acceptance Criteria**:
  - [ ] User can complete the main flows without hitting dead ends or incompatible payloads
  - [ ] Report, detail, ranking, history, and feedback surfaces share consistent score/evidence semantics
  - [ ] Legacy demo-only routes are removed or explicitly isolated

  **QA Scenarios**:
  ```
  Scenario: Main flow integration
    Tool: Playwright
    Preconditions: Primary web app running with persistence and seeded data
    Steps:
      1. Submit a GitHub repo URL from the landing page.
      2. Navigate from result page to repo detail/history.
      3. Navigate to ranking page and back to another repo detail page.
    Expected Result: Main navigation flow completes without contract or route errors.
    Evidence: .sisyphus/evidence/task-12-main-flow.png

  Scenario: API/UI contract consistency
    Tool: Bash (HTTP) + Read
    Preconditions: JSON endpoints available
    Steps:
      1. Request JSON data for a repo report/detail.
      2. Compare core fields with what the UI renders for the same repo.
      3. Assert score, risk label, evidence count, and history metadata match.
    Expected Result: UI and API use consistent source-of-truth payloads.
    Evidence: .sisyphus/evidence/task-12-api-ui-consistency.txt
  ```

- [x] 13. Add regression, integration, and E2E coverage for V1 flows

  **What to do**:
  - Expand pytest coverage for persistence/history, retrieval fallback, scoring guardrails, ranking queries, and feedback controls.
  - Add end-to-end tests for the main user journeys.
  - Ensure tests prove deferred features are not required for V1 to work.

  **Must NOT do**:
  - Do not rely only on manual smoke tests.
  - Do not skip history/search/feedback coverage because core modules already have tests.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: multi-layer test architecture and end-to-end confidence work.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `quick`: insufficient for broad regression + E2E coverage.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: FINAL
  - **Blocked By**: 3, 6, 7, 8, 9, 10, 11, 12

  **References**:
  - `projects/ai-fake-project-detector/tests/test_repo_ingestion.py` - existing ingestion tests and mocking patterns
  - `projects/ai-fake-project-detector/tests/test_structure_analyzer.py` - existing structure tests and edge cases
  - `projects/ai-fake-project-detector/tests/test_peer_retrieval.py` - retrieval regression baseline
  - `projects/ai-fake-project-detector/tests/test_scoring_engine.py` - scoring regression baseline
  - `projects/ai-fake-project-detector/templates/index.html` - landing path to cover in E2E
  - `projects/ai-fake-project-detector/templates/results.html` - report surface to cover in E2E

  **Acceptance Criteria**:
  - [ ] Test suite covers all V1-critical modules and flows
  - [ ] E2E tests cover submission, detail/history, ranking/filter, and authenticated feedback
  - [ ] Tests prove X/Twitter absence does not block V1 analysis/ranking functionality

  **QA Scenarios**:
  ```
  Scenario: Full automated suite
    Tool: Bash
    Preconditions: Test suite updated
    Steps:
      1. Run the project test command(s).
      2. Assert all module, integration, and E2E tests pass.
      3. Capture the summary output.
    Expected Result: Full V1 automated coverage passes cleanly.
    Evidence: .sisyphus/evidence/task-13-test-suite.txt

  Scenario: Deferred-feature independence
    Tool: Bash (pytest)
    Preconditions: Negative/guardrail tests added
    Steps:
      1. Run tests that exercise analysis/ranking/history without X/Twitter or anonymous feedback support.
      2. Assert the application still functions correctly for V1 paths.
    Expected Result: Deferred features are confirmed non-blocking.
    Evidence: .sisyphus/evidence/task-13-deferred-independence.txt
  ```

- [x] 14. Sync project docs and TODO to shipped behavior

  **What to do**:
  - After implementation stabilizes, update project docs so they describe the shipped V1 accurately.
  - Replace speculative TODOs with concrete next-step backlog items derived from what remains deferred after V1.
  - Ensure docs capture the chosen primary surface, retrieval strategy, scoring guardrails, ranking scope, history behavior, and feedback separation.

  **Must NOT do**:
  - Do not leave outdated docs that describe abandoned approaches.
  - Do not re-expand V1 scope during doc sync.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: final documentation fidelity and backlog curation.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `deep`: implementation choices should already be settled by this point.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: FINAL
  - **Blocked By**: 1, 12

  **References**:
  - `projects/ai-fake-project-detector/docs/PRD.md` - final product contract to sync
  - `projects/ai-fake-project-detector/docs/SOLUTION.md` - final architecture behavior to sync
  - `projects/ai-fake-project-detector/docs/PLAN.md` - high-level plan to align with implemented modules/waves
  - `projects/ai-fake-project-detector/docs/TODO.md` - backlog/status file to convert from vague notes to concrete next steps
  - `.sisyphus/plans/ai-fake-project-detector-v1.md` - authoritative execution source of truth

  **Acceptance Criteria**:
  - [ ] Project docs match the shipped behavior and deferred backlog accurately
  - [ ] `docs/TODO.md` contains actionable post-V1 items instead of stale planning placeholders
  - [ ] Docs do not contradict the primary runtime surface or V1 scope boundaries

  **QA Scenarios**:
  ```
  Scenario: Final doc fidelity check
    Tool: Read
    Preconditions: Docs synced after implementation
    Steps:
      1. Compare shipped behavior against PRD/SOLUTION/PLAN/TODO.
      2. Assert docs mention the actual primary surface, ranking scope, history behavior, and feedback boundaries.
    Expected Result: Docs accurately describe the built V1.
    Evidence: .sisyphus/evidence/task-14-doc-fidelity.txt

  Scenario: Backlog cleanliness
    Tool: Read
    Preconditions: `docs/TODO.md` updated
    Steps:
      1. Inspect TODO items.
      2. Assert remaining items are post-V1 or deferred features, not already shipped work.
    Expected Result: TODO becomes a clean next-step backlog.
    Evidence: .sisyphus/evidence/task-14-backlog-clean.txt
  ```

---

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — `oracle`
  Verify every Must Have / Must NOT Have against the implemented behavior, docs, and evidence artifacts.

  **QA Scenarios**:
  ```
  Scenario: Must-have / must-not-have audit
    Tool: Read + Grep
    Preconditions: Implementation complete and evidence directory populated
    Steps:
      1. Read this plan's Must Have and Must NOT Have sections.
      2. Inspect changed docs/code and grep for forbidden patterns such as X/Twitter-critical flow, anonymous voting, or dual-primary-surface language.
      3. Verify corresponding required deliverables exist and evidence files referenced by tasks are present.
    Expected Result: All Must Have items are evidenced; no Must NOT Have violations are found.
    Evidence: .sisyphus/evidence/final-f1-plan-compliance.txt
  ```

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run test/build/lint equivalents, inspect changed files for shortcuts, mocks left in production paths, and contract drift.

  **QA Scenarios**:
  ```
  Scenario: Quality gate review
    Tool: Bash + Grep
    Preconditions: Code changes complete
    Steps:
      1. Run `pytest` and capture output.
      2. Search production paths for leftover `MOCK_`, placeholder baselines, demo-only fallbacks, and contradictory scoring comments.
      3. Review changed files for dead/demo code in primary runtime paths.
    Expected Result: Tests pass and no quality shortcuts remain in primary production paths.
    Evidence: .sisyphus/evidence/final-f2-quality.txt
  ```

- [x] F3. **Real QA Execution** — `unspecified-high`
  Execute all task-level QA scenarios plus cross-feature flows, saving evidence under `.sisyphus/evidence/final-qa/`.

  **QA Scenarios**:
  ```
  Scenario: Cross-feature end-to-end regression
    Tool: Playwright + Bash (HTTP)
    Preconditions: Primary app running with seeded/analyzed repos and auth test user
    Steps:
      1. Analyze a repo from the landing page.
      2. Navigate to detail/history, then ranking/filter, then submit authenticated feedback.
      3. Assert score/evidence/history remain visible and feedback is supplemental only.
    Expected Result: Core V1 flow works as one cohesive product.
    Evidence: .sisyphus/evidence/final-f3-cross-flow.png
  ```

- [x] F4. **Scope Fidelity Check** — `deep`
  Ensure shipped work matches planned scope exactly and did not reintroduce deferred features.

  **QA Scenarios**:
  ```
  Scenario: Deferred-scope exclusion review
    Tool: Read + Grep
    Preconditions: Final diff/docs available
    Steps:
      1. Compare implemented surfaces against this plan's IN/OUT scope.
      2. Search for unintended additions such as public API exposure, X/Twitter ingestion, anonymous voting, comments, or appeals.
      3. Verify planned V1 items (history, ranking, search/filter, authenticated feedback) are present.
    Expected Result: No scope creep; no promised V1 item is missing.
    Evidence: .sisyphus/evidence/final-f4-scope-fidelity.txt
  ```

---

## Commit Strategy

- Prefer one commit group per wave or coherent sub-system
- Keep doc-sync commits separate from behavior changes where possible
- Require relevant pytest subsets before each commit group

---

## Success Criteria

### Verification Commands
```bash
pytest
```

### Final Checklist
- [x] All Must Have items present
- [x] All Must NOT Have items absent
- [x] TDD-added tests pass
- [x] History, ranking, search/filter, and feedback flows verified with evidence
- [x] Project docs reflect shipped V1 contract
