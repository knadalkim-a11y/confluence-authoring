# Status — v0.3.0 reference benchmark pack

Repository: knadalkim-a11y/confluence-authoring. Existing Draft PR #1.
Branch: feat/initial-authoring-skill. Preserved baseline:
`e6468aa08f55d2efbff58b328cb4c5ab5f3bb3f1`.
No main merge, Draft removal, force-push, release or Confluence publishing authorized.

## Current delivery

18 article animation cases implemented and compared against the explanatory text and
published component code, plus one clearly separate GC-pause bonus. All produce actual
self-contained macro HTML and identical preview/gallery fragments. Each has provenance,
assumptions, source/component mapping and comparison notes in examples/monitoring-cases.json.

Existing 8 recipes, 13 basic patterns, shared player and old evidence remain unchanged.
The new pack is illustrative reference material, not 19 unrestricted measured-data tools.
No stories hierarchy was introduced. Read references/monitoring-index.md.

## Actual new validation

- 30 numerical/input/render unit-test methods PASS.
- 19 generated macro fragments PASS the existing static validator.
- 19 Chromium cases PASS: intermediate property changes, playback controls,
  final/static equivalence, 320/390px and narrow-container layouts, reduced motion, print.
- Independent-instance controls, visible keyboard focus, actual event-loop pause,
  eight occupied workers at model 5s, all gallery selections/filter/search/code, and
  zero external runtime requests/script errors PASS.
- Full final browser workload rerun in 10+9 shards plus extras; merged with test and
  artifact SHA256 checks. Contact-sheet generation also handles a fresh partial shard.
- Wide/middle/final/narrow output screenshots and the gallery visually reviewed.
- Numerical and synchronization issues found during review were corrected and retested.

Evidence: tests/monitoring-verification.json and tests/monitoring-browser-report.json.
Reproduce using references/monitoring-tests.md. Generated dist is not tracked.

## Optimization

Same final inputs/prefixes, no model or data thinning: 19 macro outputs shrink from
1,681,158 to 1,228,380 UTF-8 bytes (26.93%) through redundant collinear CSS keyframe
removal. One active gallery preview avoids running all cases simultaneously.
This is neither an old-vs-new version size comparison nor an FPS/gzip claim.

## Verification boundaries

Original live website A/B: NOT VERIFIED. Original text and published code were inspected;
only our output was rendered in the local browser. Target Confluence rendering:
NOT VERIFIED. No page was edited. No visual-equivalence or reader-comprehension score.

Container could not resolve github.com; source reads/writes used the authorized connector.
Local source-snapshot checks are not a fresh git-clone or CI check. Historical v0.2 tests
were preserved but not all rerun; their previous results remain historical evidence.
GitHub Actions is not configured. Cross-browser behavior and real frame-rate are unmeasured.
Lint is not a security sanitizer. All new reference outputs are synthetic; descriptions
must not turn illustrative geometry into measured data or correlations into proven causes.
