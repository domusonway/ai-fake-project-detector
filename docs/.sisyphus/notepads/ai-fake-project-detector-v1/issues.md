## Notepad: Issues

- Fixture set now uses three labeled offline cohorts (substantive, hype_heavy, early_but_real) plus a deterministic peer-baseline builder; future history/ranking tests can reuse the same shapes without network calls.
- Diagnostics cleanup: the fixture package now uses TypedDict-backed exports and the changed tests avoid TypedDict mutation/deletion patterns that triggered type-check noise.
- Cleanup pass: switched changed tests to explicit relative fixture imports and lightweight casts so diagnostics stay quiet without changing offline fixture behavior.
- Micro-fix: removed remaining invalid casts by using direct fixture values and a simple None check for repo license payloads.
- F2 blocker fix: canonical results page now uses Chart.js-compatible `type: 'bar'` with `indexAxis: 'y'`, removing the removed `horizontalBar` runtime path.
