# Status — v0.18.0 (monitor-only by default; aligned stacked rows; layout notes)

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
  e.g. an AI agent call or RAG; `current` / `proposed` shown in the picture), `concept` (presets) and
  `compose` (a nested tree of layout containers and parts for any other idea). Static or
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

- Unit: `python -m unittest discover -s tests` — 111 tests pass (v0.11.0).
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

## v0.18.0 feedback from first internal use

An in-house Claude Code built a compose figure on Windows 11 from the repository link. Its feedback (unaligned
stacked rows, no alignment criterion, invisible layout decisions, `grow` docs) was reproduced and fixed in the
engine; phone support became opt-in (`--phone`). Actual results (2026-10-06, Chromium 141): unit 124 OK; 62/62
figures --check; browser_live 18/18 default and NanumGothic; 10 examples under NanumGothic; monitoring, smoke,
gallery pass; metrics on 48 figures: only the reproduction changed (near misses 14 → 0).
Not verified: Windows 11 font widths; whether the layout notes help the in-house agent.

## v0.17.1 diagram restored, clutter measured

v0.17.0 moved diagram onto the compose engine and reported it "comparable"; the user saw it was busier, and the new
clutter metric agreed (bends at 715 px +43%, crossings on phones 0 → 3, compose figures affected too). Reverted the
move and the rules added for it; kept the compose parts and three fixes for real gate findings. All 46 measured
figures now have the v0.16 clutter numbers.
Actual results (2026-10-06, Chromium 141): see the verification list in the PR (unit, 61/61 --check, browser_live
both fonts, monitoring, smoke, gallery).

## v0.16.0 composition engine

`compose` kind (`visuals/live/scenes/compose.js`, `visual_spec.compose_data`); concept forms are presets of it and
`concept.js` is gone. New layout gate (no link through another box; boxes and frames nest). Evaluation in design
doc §12: dev set 9 figures rebuilt (judged: 5 missed→comparable, 2 weak→comparable, b01 missed→weak (tangle
metaphor out of scope), b03 stays weak). Held-out 8 topics, specs written once after the engine: first try gates
4/8, judged good 3 / flawed 5 / missed 0; the 5 flaws were engine rules (label placement, tree routing, phone
height and edge room), fixed in the engine with the specs unchanged, 8/8 after (that second number is not an
independent result). All judgements are mine, not the user's.
User review (2026-10-05, dist/compose-compare.html): the engine-fixed figures explain better. This is an overall
verdict on the comparison page, not a per-figure score.
Actual results (2026-10-05, Chromium 141): unit 120 OK; examples 22/22 with --check; compose examples 7/7 under
--font NanumGothic; browser_live 18/18 default and 18/18 NanumGothic; browser_monitoring and
browser_smoke pass; browser_diagram_layout SKIP (no CSS layout case). Local review page: dist/compose-compare.html.

## v0.15.1 external-topic test

21 figures from kciter.so sections (local only): 18/21 first build, 21/21 after two library fixes (green tone
contrast, phone compare height). Side-by-side judgement (mine, not the user's): 12 comparable, 3 weaker, 6 miss the
point; gaps listed in design doc §11. Actual results: unit 118 OK; browser_live 18/18 default and NanumGothic;
examples 18/18 under both fonts; browser_monitoring and browser_smoke rc 0.

## v0.15.0 design phase 3

Survey of all 61 kciter.so posts (design doc §10): interactive demos exist in 5 posts (58 demos); 229 figures
from 17 image-heavy posts reviewed (mostly photos, screenshots, code). Built from that: role tones for diagram
components and boundary groups, and the `concept` kind (compare, stack, sequence) with default choreography.
Screenshot review (not the gates) found an arrow label clipped by a column, a message number wrapping alone and a
stack over the height budget; fixed in the kind (the label is now gated as free text).
Actual results: unit 117 OK; browser_live 18/18 default and NanumGothic; examples 18/18 with --check under both
fonts (3 new concept examples); browser_monitoring and browser_smoke rc 0; example gallery built.
DDD explainer rebuilt locally with 5 visuals (dist/ddd-ai/v2, before/after sheet dist/ddd-ai/ddd-before-after.png).
Not verified: whether the concept figures reach the reference demos' quality (the user's call); the new examples
were written by the same AI that built the kind, so they are weak evidence of first-try generality.

## v0.14.0 design phase 2 done

Durations moved to seconds on screen (a 0.13.0 claim corrected: the diagram transition was ~1.6 s on screen,
not 0.5 s). trend, flow, cascade and thread-pool now use cues and fades; the gate also fails one-frame
appearances. Defects the gate found are listed in docs/CHANGELOG.md 0.14.0 (including duplicate flow token ids).
Actual results: unit tests OK; browser_live 18/18 default and 18/18 NanumGothic with no warnings; examples
15/15 with --check under both fonts; browser_monitoring and browser_smoke rc 0. Frame sheets (local):
dist/cascade-before-after.png, dist/trend-reveal-before-after.png. Not migrated: bars, share, timeline
(static by default), distribution (its own fades since 0.10.1, not keyed), cfs, eventloop, timeout.
Not verified: the user's judgement of the motion.

## v0.13.0 design phase 2, diagram first

Diagram step changes are cues (fade back, then rise at 80%, one pop, token leaves with the rise). New gate:
a keyed colour/width jump in one frame fails choreographed kinds, warns for others. Gate checked against the
same diagram with cues removed (fails) and with cues (passes). Actual results: unit tests OK (new
tests/test_choreo.py); browser_live 18/18 default and NanumGothic; examples 15/15 with --check under both fonts;
browser_monitoring and browser_smoke rc 0. Frame-by-frame before/after of the agent diagram's step 2->3
(local, dist/step-switch-before-after.png). Remaining for phase 2: cascade states, status numbers, trend event
labels, distribution markers, flow/thread-pool state colours. Not verified: the user's judgement of the feel.

## v0.12.0 design phase 1 (docs/design/motion-concept-architecture.md)

Kit motion math added; scenes' presentation motion moved onto it. The existing speed gate failed two
visuals on the first curve choice (diagram token 561 px/s, thread-pool queue 537 px/s); fixed by making
inOut the symmetric smoothstep. Actual results: unit tests OK (1 new: closed forms, spring vs numeric
integration within 0.002); browser_live 18/18 default and 18/18 NanumGothic; 15/15 examples with --check
under both fonts; browser_monitoring and browser_smoke rc 0. Visible change is small by design; phase 2
(cue-based state transitions) is where transitions stop snapping. Not verified: the user's judgement.

## v0.11.0 generality pass (why: per-case fixes do not reach the next visual)

The user's review found three problems by eye (#10 too-fast spin, #2 abrupt entry, #9 crooked
LB wires); 0.10.1 fixed each inside its own scene. The user pointed out that this is whack-a-mole.
This pass moved the rules into shared kit parts and a gate that runs on every live visual.

- Measured first on the article demos (local, not committed) with a pixel "instant change"
  metric: the demos have single-frame changes of 4,000-27,000 px² too (state switches, loop restarts),
  so that metric does not separate good from bad motion and is NOT gated. Token speed and wire
  shape are gated (`visual_gates.MOTION_JS`, 30 frames per wall second, rate map included, 715 and
  360 px): token <= 480 px/s, no diagonal `K.wire` segment, no moving dot outside `K.token`.
- Check that the gate catches the reported defect: the pre-fix event loop (7cc0df3) with its rotor
  tagged as a token measures ~3,000 px/s (fail). The pre-fix cascade and event loop also fail as
  "moving dot not a token" (they drew dots by hand). The pre-fix cascade's diagonal wires are not
  detectable after the fact (they were not `K.wire`); new wires cannot be diagonal by construction.
- Applying the rules to everything found unreported instances: all three diagram examples had
  diagonal connectors; thread-pool inflow ~860 px/s; support-backlog tokens at the limit under its
  1.6x rate map (flow token speed is now capped in wall terms from the rate map).
- Regression found by screenshot (not by a gate) and fixed: slower event-loop arrivals landed on
  top of queued requests; arrivals now go to their own slot and the queue closes up over 0.2 s.

Actual results (Linux, Python 3.11, Node 22, Playwright 1.56.0 + Chromium 141):
- Unit: `python -m unittest discover -s tests` — 111 tests pass (2 new: kit parts, orthogonal wires
  at 720/600/360 px for cascade and the three diagram examples).
- `tests/browser_live.py`: 18/18 pass; `--font NanumGothic --output dist/live-nanum`: 18/18.
- `scripts/build_visual.py <spec> --check` for the 15 examples: 15/15 exit 0, again 15/15 with
  `--font NanumGothic` (support-backlog failed the new speed gate first; fixed as above).
- `browser_monitoring.py` rc 0 (suite built with `--baseline dist/baseline-v0.5.0`),
  `browser_smoke.py` rc 0, `browser_diagram_layout.py` SKIP (no CSS layout case left).

Not verified: whether the user finds the new pace and elbow routing better (the gates check
limits, not taste); 480 px/s is my chosen limit, not measured on readers; target Confluence;
macOS/Windows fonts. Generality to new topics is still measured only by my own runs.

## v0.10.0 reference parity (done for all 18; quality judgement pending)

All 18 in-article cases run on the live tier and were compared side by side with the article's
demos (`dist/ref18/compare-all.html`, local only: originals are recorded, not committed). New:
`distribution` kind, trend `stream`/`log`/2 x 2 grid, custom scenes cfs, cascade, eventloop,
timeout. The cascade model now ends on the last saturated server (the old CSS model let all
three fail); event-loop and timeout keep their model times. browser_diagram_layout.py now reports SKIP
(no CSS layout case left) and browser_monitoring.py retired its CSS event-loop rotor check. Whether each case reaches the
demos' quality is for the user to judge from the comparison page.

## v0.9.2 reference parity (batch 1)

All 18 article demos were captured and paired with ours (same 673 px width, 2x). Six cases now
follow the demos (thread-pool, pipeline-bottleneck, bounded-queue, cpu-latency,
slow-degradation, postmortem-timeline). The other 12 still use the CSS tier and read as
dashboards; they are the remaining work. Gates: unit 109, 15/15 examples and 6/6 live under
both fonts, CSS suites pass. Whether the six now match the demos' quality is for the user to
judge from the pairs.

## v0.9.1 focus pass

The user judged the output below the article demos. A same-scale side-by-side (673 px
column, 2x) confirmed it: our scenes were 2-3x taller, stacked secondary charts and legends
on the mechanism, used 11-13 px type where the demos use 13-15 px, and drew busy state as
outlines. Changes in docs/CHANGELOG.md 0.9.1; afterwards all gates pass again (unit 108, 15/15
examples and 4/4 live under both fonts, CSS suites). Still different: the font (Pretendard is
not shipped), and the judgement "now comparable" is mine, not the user's.

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
