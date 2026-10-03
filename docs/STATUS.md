# Status — v0.9.0 document visuals: architecture and process diagrams

Review branch: `feat/initial-authoring-skill`, Draft PR #1. No main merge, Draft removal,
release or Confluence publication.

## Goal

When someone wants a visual for a report or document, the AI produces one that fits the
situation at the quality of the live tier. Monitoring cases are validation material.

## What exists now

- Spec path (default in SKILL.md): `references/visual-specs.md` → JSON spec →
  `scripts/build_visual.py --check` → `macro.html`, `preview.html`, `figure.svg`,
  `figure.png`, screenshots. Kinds: `flow` (backlog, queue, capacity, bottleneck, 1 lane or
  2 variants), `trend` (metrics over time, events, thresholds, columns), `bars` (comparison,
  before/after, funnel), `share` (composition and its change; no pie charts), `timeline`
  (dates, numbers or `HH:MM` clock times, durations, incident legends), `diagram` (components
  in layers, connections, groups; with `steps` the path a request, document or approval takes,
  e.g. an AI agent call or RAG; `current` / `proposed` shown in the picture). Static or
  animated is chosen by situation; `motion: "none"` gives a no-script figure.
- Every recipe in `recipes/` names the kinds that usually fit it (status, architecture,
  design, incident, comparison, tutorial, weekly report, handoff).
- The spec layer validates honesty (`source`, `data_kind`), unknown keys/events/placeholders,
  bottleneck rules, caption readability; numbers in text come from the model. Static kinds
  print "예시 데이터" / "추정값" inside the picture when the data is not measured.
- Shared browser gates (`scripts/visual_gates.py`): overlap/clipping at 24 moments × 2 widths,
  painted-over text, contrast ≥ 4.5:1, text ≥ 9 px, height budgets, captions on events,
  future-label leaks, model equality, controls, reduced motion, print, two blocks, no-JS on
  phones, no external requests, text inside its box and connection labels off boxes;
  `--font` repeats them under another installed font.
- Without Playwright or Chromium the build still writes macro/preview/SVG and exits 2
  ("BUILT (unchecked)") so an unchecked visual is never reported as checked.
- 15 report-style examples in `examples/visuals/` (3 diagrams: AI agent request path, RAG
  indexing, AI adoption approval); pipeline-bottleneck, bounded-queue and
  cpu-latency are specs of the same kinds; thread-pool is the custom-scene example.

## Actual validation (Linux, Python 3.11, Node 22, Playwright 1.56.0 + Chromium 141)

Fonts: Noto Sans CJK KR (default stack) and NanumGothic (forced with `--font`).

- Unit: `python -m unittest discover -s tests` — 108 tests pass.
- `tests/browser_live.py`: 4/4 live monitoring cases pass all gates; again 4/4 with
  `--font NanumGothic --output dist/live-nanum`.
- `scripts/build_visual.py <spec> --check` for each of the 15 example specs: 15/15 exit 0;
  again 15/15 with `--font NanumGothic`. `build_visual_gallery.py examples/visuals` builds the
  review page.
- Exported `figure.svg` is now gated too (`--check`: text inside the figure, no overlap, nothing
  painted over, contrast; also under `--font`): passes in all example builds. The first check of
  the exports found that a 90-char `source` ran 79 px off the left edge; the source line now
  wraps (≤ 3 lines, then "…"), with a unit test. The gate was shown to catch injected
  out-of-bounds and overlapping text.
- No-browser path: Playwright hidden (`sys.modules`) → exit 2 with macro, preview, SVG and
  report; `--browser /nonexistent/chromium` → exit 2.
- `browser_monitoring.py` (15 CSS cases), `browser_smoke.py`: pass.
  `browser_diagram_layout.py`: pass after building the suite with
  `--baseline dist/baseline-v0.5.0`; the first run failed because I built without
  `--baseline` (documented precondition, now asserted with a message).
- The NanumGothic runs found no failure that the default font did not also show. The override
  does apply (computed family NanumGothic; a sample label 51.5 → 52.5 px wide), but the two
  fonts' metrics are close, so this is weak evidence for macOS/Windows fonts. The final run
  caught a regression of my trend label placer at 360 px under both fonts; fixed before the
  counts above.

## Diagram kind: how it was checked (v0.9.0, same AI, not independent)

- First build of the agent example failed the gates: step badges on labels and boxes, and
  700 px tall at 360 px (budget 600). Fixed by putting step numbers on the connection labels,
  widening crowded gaps, and tighter phone spacing; the new box gate caught each case.
- Four deliberately hard specs (5-layer approval process with a feedback lane, 4 sources
  fanning into one store, 14-char names, a 2-component minimum) passed the gates on first
  build. Screenshot review still found: the moving token crossed a box's text between two
  connections, a step could not say "both reviews at once", and the dashed-line legend
  could only mean "비동기·선택". Fixed (token skips box interiors, `paths`, `dashed_means`).
- Not covered by `diagram`: free placement, swimlanes, sequence diagrams, cycles drawn as
  circles, groups that are not whole layers, more than 5 layers or 4 components per layer.
  Large diagrams on phones hit the 600 px budget; split them.

## Generality self-run (same AI, not independent)

Six report requests written from the docs only: inquiry backlog, sign-up funnel, incident
timeline, infrastructure cost mix, API latency (estimate), release notes. Release notes →
no visual (prose), as the guidelines say. First try: 2/5 specs passed the gates, and both of
those still had problems visible only in screenshots.

- Spec layer blocked my caption bound to `wait:1`, which never happens in that model.
- Gate failures (library defects, fixed): milestone labels overlapping at 360 px, x-tick
  collisions, value labels colliding, a node name touching its capacity label, the backlog
  history strip touching the legend, browser 213.3 vs model 213.2 (JS half-up vs Python
  half-even rounding).
- Screenshot-only findings (gates passed): "가장 많이 이탈" could mean the lowest conversion or
  the most people lost (funnel now shows both, `drop` picks); cost categories hard to tell
  apart (names inside segments, bordered swatches); an incident drawn with schedule words
  (`legend: false`, `status_labels`); a "29/29일" counter that added nothing (removed); data
  kind visible only in notes (now in the picture).
- After fixes all five pass; funnel, incident timeline and cost share became examples.

## Known limits (not hidden)

- The self-run was done by the AI that wrote the library and docs. A fresh session following
  only SKILL.md with a real report topic is the stronger check; it has not been done.
- Not covered: maps, free-form graphs (see the diagram limits above), scatter/correlation, distributions beyond the
  monitoring percentile case, > 2 variants, mixed units in one chart.
- Whether a caption's sentence matches the picture is checked only in the screenshot review.
- Fonts: Noto Sans CJK KR and NanumGothic only. Apple SD Gothic Neo (macOS) and Malgun Gothic
  (Windows) not tested. `figure.svg` uses the viewer's fonts; `figure.png` is fixed pixels.
  Opening the SVG/PNG in PowerPoint, Keynote or Word was not tested.
- Target Confluence: inline scripts, CSP, editor, mobile, PDF export NOT verified. Static
  output (`motion: "none"`, bars, share, timeline) needs no script.
- The 15 CSS-tier monitoring cases and the 13 legacy CSS patterns keep the older look.
