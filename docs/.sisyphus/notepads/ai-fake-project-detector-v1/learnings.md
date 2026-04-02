## Notepad: Learnings

- 2026-04-01: Contract alignment must keep score semantics single-directional: `fake_risk_score` and `dimension_scores` are both risk-oriented (higher = more suspicious), while `structure_score` remains goodness-oriented and must not be mixed with risk meaning.
- 2026-04-01: V1 peer retrieval should stay rule-first; embedding/hybrid are optional enhancements and must define explicit fallback behavior for sparse/low-confidence peer baselines.
- 2026-04-01: Peer retrieval now ranks directly comparable peers before deterministic fallback peers and emits machine-readable `retrieval_metadata` so scoring/detail/ranking flows can consume confidence, sample-size, sparse-peer, and disclosure signals without re-deriving them.
- 2026-04-01: Retrieval cleanup removed bare generic `dict` annotations from the module while preserving the rule-first ranking, fallback disclosures, and `retrieval_metadata` contract.
- 2026-04-01: Final T6 cleanup removed accidental project-doc status writeback from `projects/.../docs/PLAN.md` without changing retrieval behavior or tests.
- 2026-04-01: Scoring calibration should treat peer uncertainty and small-project immaturity as guardrails, not direct penalties—peer-gap must be downside-only and confidence-gated, while early-but-real repos with tests/docs/license should stay out of inflated risk bands.
- 2026-04-01: For test-only typing cleanup, prefer local TypedDict wrappers plus a typed helper around dynamically inferred functions; this removes operator/index/lower/len noise while leaving only repo import-layout warnings.
- 2026-04-01: For implementation-side typing around nested metadata, extract raw Mapping values first and coerce through tiny helpers before calling `int`/`str`; this preserves behavior and removes object-union conversion errors.
- 2026-04-01: V1 regression tests need to lock the full landing → analyze → detail/history → rankings → feedback path, because deferred social features and feedback weighting are easiest to accidentally couple across surfaces.
- 2026-04-01: For TypedDict-based tests, route helper calls that expect plain dicts through `cast(object, value)` first to avoid invalid-cast diagnostics without changing behavior.
