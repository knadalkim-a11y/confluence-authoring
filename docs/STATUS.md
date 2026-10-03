# Status — v0.7.0 spec-driven document visuals

Review branch: `feat/initial-authoring-skill`, Draft PR #1. No main merge, Draft removal,
release or Confluence publication.

## Goal

When someone wants a visual for a report or document, the AI produces one that fits the
situation at the quality of the live tier. Monitoring cases are validation material.

## What exists now

- Spec path (default in SKILL.md): `references/visual-specs.md` → JSON spec →
  `scripts/build_visual.py --check` → `macro.html` + screenshots. Kinds: `flow` (backlog,
  queue, capacity, bottleneck, 1 lane or 2 variants), `trend` (metrics over time, events,
  thresholds, columns), `bars` (comparison, before/after), `timeline` (schedule). Static or
  animated is chosen by situation; `motion: "none"` gives a no-script figure.
- The spec layer validates honesty (`source`, `data_kind`), unknown keys/events/placeholders,
  bottleneck rules, caption readability; numbers in text come from the model.
- Shared browser gates (`scripts/visual_gates.py`): overlap/clipping at 24 moments × 2 widths,
  painted-over text, contrast ≥ 4.5:1, text ≥ 9 px, height budgets, captions on events,
  future-label leaks, model equality, controls, reduced motion, print, two blocks, no-JS on
  phones, no external requests.
- 9 report-style examples in `examples/visuals/` (all gates pass); pipeline-bottleneck,
  bounded-queue and cpu-latency are specs of the same kinds (same model numbers as before);
  thread-pool is the custom-scene example.

## Actual validation (Linux, Python 3.11, Node 22, Playwright 1.56 + Chromium 141, Noto Sans CJK KR)

- Unit: 102 tests pass (incl. `tests/test_visual_spec.py`).
- `tests/browser_live.py`: 4/4 live monitoring cases pass all gates.
- `scripts/build_visual_gallery.py examples/visuals --check`: 9/9 specs pass all gates.
- `browser_monitoring.py` (15 CSS cases), `browser_smoke.py`, `browser_diagram_layout.py`: pass.
- Generality test: three report requests not prepared in advance (API incident, nightly
  batch, cloud cost), specced from the docs. First try: 1/3 passed. Failures were library
  defects (percent decimals ignored, label collision, a gate formatting mismatch, final state
  not gated, stale screenshots kept) and one authoring error only visible in screenshots (a
  caption claiming a backlog remained after the model drained it). All fixed; added to examples.

## Known limits (not hidden)

- The generality test was done by the same AI that wrote the library and docs; it is not an
  independent test. A fresh session following only SKILL.md is the stronger check.
- Kinds cover queues/flows, time series, bar comparisons and schedules. Not covered: maps,
  networks/graphs, distributions beyond the monitoring percentile case, funnels as a kind,
  >2 variants, mixed units in one bar chart.
- Semantic correctness of captions (does the sentence match the picture) is checked only by
  the screenshot review step, not by gates.
- Fonts verified with Noto Sans CJK KR only; Apple SD Gothic Neo / Malgun Gothic not tested.
- Target Confluence: inline scripts, CSP, editor, mobile, PDF export NOT verified. Static
  output (`motion: "none"`, bars, timeline) needs no script.
- The 15 CSS-tier monitoring cases and the 13 legacy CSS patterns keep the older look.
