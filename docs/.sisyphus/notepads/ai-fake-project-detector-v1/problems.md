## Notepad: Problems

## 2026-04-01 Task: T3 fixture dataset blocker
Focused pytest passes and the offline fixture layer is functionally reusable, but basedpyright still reports errors in changed test files (`test_scoring_engine.py`, `test_repo_ingestion.py`, plus legacy-style module imports in tests). After 3 retries in the same session, T3 is treated as blocked on typing/import hygiene rather than behavior. Continue independent Wave 1 tasks and revisit later if stricter Python diagnostics become a release gate.
