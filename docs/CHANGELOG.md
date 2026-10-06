# Changes

## 0.17.1 — diagram restored; clutter is measured

- Correction to 0.17.0: moving `diagram` onto the compose engine made the figures busier, not "comparable" as I
  reported. Measured on 46 figures with the new `scripts/figure_metrics.py`: bends at 715 px 74 → 106 (+43%),
  connector crossings on phones 0 → 3; compose figures were affected too (straight links became elbows). The gates
  passed because they check defects, not clutter.
- `diagram` is back on its own scene (`visuals/live/scenes/diagram.js`, v0.16 builder). The routing and layout rules
  added for the move are removed (spread ports, bend placement, two-line names to fit a row, min-aware sharing,
  folded-row transpose, over/under detours, centred stretched frames, crowded-gap widening, leftover width to gaps,
  bottom-detour label room). Kept: the compose parts (path steps, step list, legend, dashed, bar, badge per state)
  and three fixes for real gate findings (wrapped-name spacing, group names as taken label places, side-gutter
  relayout on phones only).
- Result: all 46 measured figures have the same clutter numbers as v0.16; 61/61 pass the gates; 10 examples look the
  same side by side (diagram 3, compose 7).
- `build_visual.py` writes the clutter numbers into `report.json`; a layout or routing change is accepted only when it
  does not make the measured set busier than its baseline (AGENTS.md).

## 0.17.0 — diagram on the composition engine; remaining gaps

- `diagram` is now a compose preset (`visuals/live/scenes/diagram.js` removed; one implementation for every
  structure and idea figure). The spec is unchanged: layers → columns, groups → dashed frames, types → tone and
  shape plus legend, steps → path steps with the step list in the picture.
- New compose parts (generic, documented in visual-specs.md): step `path`/`paths` (route highlight + one dot),
  `step_list`, `legend`, element `dashed` and `bar` (relative amount), and a badge that changes with the state
  (`set: {id: {state, badge}}`, swapped old-out/new-in).
- Engine rules found while moving diagram (each fixed once in the engine, then all figures rebuilt):
  rows try names wrapped onto two lines before wrapping the row; containers in a row get their minimum and share
  the rest; leftover width goes back to narrowed gaps first; a gap with many labelled links widens; a frame
  stretched to its row's height centres its content; a folded row turns its columns into rows; blocked links also
  go over or under; runs bend next to their target, fan-outs next to their source, two-way pairs at one x; ports on
  a crowded left/right side spread evenly and the box grows when needed; a bottom detour reserves room for its
  label; group names and separator words are taken places for link labels; the side-gutter relayout is phone-only.
- Old vs new: ai-adoption-approval comparable or clearer, rag-indexing comparable, ai-agent-request first worse
  (empty frame, bunched fan-out labels), then comparable after the port and gap rules (my judgement).
- Examples: abstraction-layers (bars); tool-approval now swaps its chip on approval.

## 0.16.0 — composition engine (design phase 4)

- New kind `compose`: a figure is one tree of layout containers (`row`, `column`, `grid`, `stack`, `split`,
  `lifelines`, nesting up to 4 deep) and parts that work in every container: elements (`box`, `pill`,
  `cylinder`, `doc`; states `normal`/`selected`/`muted`/`error`/`ok`; `sub`, `code` lines, `badge`, `bubble`),
  container frames and annotations (`frame` solid/dashed, `label`, `note`, `banner`, `span`, `bracket`, `sep`),
  and links (`flow`/`reply`/`hidden`/`fail`/`none`, labels, `via`). `steps` show parts, change states (animated
  cues) and bind captions; without steps each top-level part enters in turn.
- Layout is measured, not templated: natural widths for elements, rows narrow their gaps, then wrap into even
  lines (snake order for a chain), then fold; splits size sides by need; links route orthogonally from the
  laid-out boxes (elbow in the gap between branches, shared trunk for fan-out, around the side when a box is in the
  way, side gutter on phones); labels take the first free place.
- `concept` compare/stack/sequence are now presets that expand into a compose tree; `visuals/live/scenes/concept.js`
  is removed (one implementation). Their spec is unchanged.
- New gate `LAYOUT_JS` for every visual: a link with `data-ends` may not run through another box; boxes and frames
  nest or stay apart. Shown to fail a forced bad route; it found a real defect (stack bands overlapping by a few px).
- Examples: mcp-tool-call, tool-approval, prompt-caching, multi-agent. Unit tests: compose validation, steps/state
  cues, static layout invariants at 715/600/360 px for every compose example.
- Evaluation (design doc §12): dev set (9 weak/missed figures from the v0.15.1 test) rebuilt; held-out set (8
  topics fixed before implementation, specs written once): first try 4/8 gates, judged good 3 / flawed 5 / missed 0;
  the 5 flaws were engine rules, fixed in the engine, 8/8 after (no longer independent).

## 0.15.1 — fixes from an external-topic test

- 21 figures built from the gist of kciter.so sections (design doc §11): 18/21 first build, 21/21 after fixes.
- Fixed in the kit/kind: the green role tone's text was 4.37:1 on white (now #237032, 6.1:1; a unit test checks all
  tones on white and on their fills); a 3-column compare on phones exceeded the height budget (many items now sit
  two per row on phones).

## 0.15.0 — concept vocabulary (design phase 3)

- Reference survey of all 61 kciter.so posts (design doc §10): interactive demos in 5 posts; the concept
  demos tell roles apart with soft tinted boxes and use forms we did not have.
- Role tones (`K.TONE`: blue, green, amber, purple, red, gray; soft fill + same-hue border). Diagram
  components take a tone from their type or their own `tone`; a group with `tone` is a dashed boundary.
- New kind `concept`: `compare` (columns, arrow label, notes), `stack` (bands, bracket, free space),
  `sequence` (actors, lifelines, numbered messages). Default choreography: units enter in turn.
- Examples: rag-before-after, agent-context-window, agent-tool-call; ai-agent-request shows its 사내망
  boundary. Screenshot review found and fixed: an arrow label clipped by a column (gap now fits it, label
  gated as free text), a message number wrapping alone, stack height over budget (bands share a fixed
  budget; name and sub share a line when wide enough).

## 0.14.0 — choreography for trend, flow, cascade, thread-pool (design phase 2 done)

- Cue durations are seconds on screen, converted through each case's rate map (`choreo.cue(..., rate)`,
  `K.wall`). Correction: the 0.13.0 diagram transition was about 1.6 s on screen, not 0.5 s.
- trend: reveals at one moment enter in sequence (event line drops in, label, annotations, bands, log);
  pills and notes swap (old out, then new in); a reveal at the very end gets a settle tail.
- cascade: card warn / health-check / removed levels and DB slowing are cues; status words swap; two alarm
  pulses on failure; shares and DB latency glide (`K.approach`).
- flow: queue onset/drain (from the model) blends the bottleneck, gauge, queue box and spare pill;
  thread-pool: dependency slow/recover blends, and its dots keep their phase through the speed change.
- The gate now also fails a keyed element that appears fully opaque in one frame. It found and we fixed:
  fast-opacity event lines, a reveal at the final frame, the queue box/label popping in, a rising label
  crossing a value label, and duplicate flow token ids (same arrival time; two lanes sharing ids).
- Annotation timing gate: present within 0.6 s on screen of its event (still absent before it).

## 0.13.0 — choreography layer (design phase 2), diagram first

- `scripts/choreo.py` builds and validates cues (duration range per property role, no overlap, continuity,
  settled before the final scene); `visuals/live/choreo.js` evaluates them, pure in T.
- Diagram steps no longer switch in one frame: the old step fades back (0.25 s, in), the new path, boxes and
  list item rise at 80% of that fade (0.3 s, out), a joining box pops once, the token leaves with the rise,
  and the last 0.5 s settles into the final scene (diagram `end` = steps + 0.5).
- Gate: keyed (`data-k`) colour or width jumping in one frame fails choreographed kinds, warns for the rest.
  Checked: the same diagram with its cues removed fails; with cues it passes.

## 0.12.0 — motion math in the kit (design doc phase 1)

- `docs/design/motion-concept-architecture.md`: reviewed design (choreography layer, concept vocabulary);
  decision 1 approved (kinds own default choreography; specs pick a motion level, not cues).
- Kit: easing set `K.CURVE` (out for entrances, in for exits, symmetric inOut for moves), `K.DUR`, `K.tween`,
  closed-form `K.spring`/`K.pop`, `K.approach`, `K.stagger`, `K.wave`/`K.saw`, `K.mix`. All pure in T.
- Scenes: presentation motion moved onto the shared curves; data interpolation left on the model.
- The 0.11 speed gate caught the first inOut choice (peak ~2.4x average: 561 and 537 px/s); inOut is smoothstep.

## 0.11.0 — motion and wiring become shared parts with gates (not per-case fixes)

The three problems the user found by eye (#10 spin, #2 abrupt entry, #9 crooked wires) were each
fixed inside one case in 0.10.1. This release turns them into rules every visual inherits:
- Kit parts: `K.ortho` + `K.wire` (orthogonal connectors), `K.token` + `K.at` + `K.M` (one pace
  for moving things), `K.ease` (appearances), `K.follow` (data-riding markers).
- Gate `MOTION_JS` for every live visual: token speed <= 480 px/s, no diagonal wire, no moving
  dot outside `K.token`. On the pre-0.10.1 event loop it reports ~3,000 px/s (fail).
- Applying the rules everywhere found the same defects in places nobody had pointed at:
  all three diagram examples had diagonal connectors (now straight where boxes face each other,
  otherwise one elbow, fan-outs on one spine, bends kept outside group boxes, phone gaps sized
  by real bends); thread-pool inflow ran at ~860 px/s; event-loop arrivals and responses were
  quick 0.25-0.35 s slides. All now take the shared pace.
- Measured and not gated: a pixel "instant change" metric. The article demos switch as abruptly
  as ours, so it did not separate good from bad motion.

## 0.10.1 — fixes from the user's review of the comparison page

- event-loop: the loop turned once per task (tasks take ~0.08 s, so it spun); it now turns at a
  steady pace with a fading trail and freezes while the CPU task holds it.
- percentile-comparison: dots popped into place; they now drop from the top onto their stacks,
  percentile lines are drawn downwards and their labels fade in; the tail band fades in, no frame.
- cluster-cascade: LB-to-server wires were diagonals of different slopes; they are now one trunk
  with square branches (DB side too). On phones a spine runs down the edge so no wire crosses a card.

## 0.10.0 — all 18 article cases rebuilt after the reference demos

- Every in-article case now runs on the live tier and was compared side by side with its
  reference demo (same width, 2x; dist/ref18, local only). Only gc-pause (bonus) stays CSS.
- New kind `distribution` (dots per observation, mean / P50 / P95 / P99 in sequence, tail band
  with computed share). `trend` gains a 2 x 2 grid, per-column events, helper series (dashed,
  dots, no label), a request `stream` strip, a `log` strip, hidden panel labels, soft pill tones.
- Custom live scenes for mechanisms no kind expresses: `cfs` (CPU quota throttling),
  `cascade` (load balancer domino), `eventloop` (Node.js loop blocked by CPU work), `timeout`
  (gateway 504 vs backend 200). Their numbers come from Python models.
- Gates: a dense overlap sweep at 600 px as well (found a clipped CPU note and a diagram label on
  a box); diagram switches to the phone layout when its row would be too tight; annotations
  avoid event labels; value labels are skipped when no free spot exists.
- Tests that meant "a CSS-tier case" now use gc-pause; model-number tests kept by exporting the
  same numbers from the new specs; svg-id uniqueness is now checked for every case.

## 0.9.2 — reference parity, batch 1

- Captured all 18 article demos (not only 4) and paired each with ours at the same width and
  scale (dist/ref18, local only). Finding: the 14 CSS-tier cases read as dashboards (cards,
  buttons, KPI tiles, 3-5x taller) while the demos are one chart with direct annotations.
- `trend` gains the demos' vocabulary: coloured event lines with stacked labels, bands with a
  computed `{duration}` bracket, annotations at series values, shading between two series,
  column titles, partial series, `_start` / `_change_pct` placeholders.
- slow-degradation and postmortem-timeline moved to the live tier as trend specs (same model
  numbers: +72%, 18 / 3 / 29 minutes), matching the demos' layout.
- Fix found by the validator: a variable named `top` tripped the forbidden-API lint (`top.`);
  event lines were hidden under the panel background.

## 0.9.1 — focus pass after a same-scale comparison with the article demos

- Thread pool shows only the mechanism (inflow, queue, pool, slow DB); the two charts under it
  were a second claim and are gone (height 472 → 258 px). Busy slots are solid blue; the status
  line has three items.
- Flow chain: compact red queue right in front of the bottleneck, no "한도 도달" pill on the
  already-red box, history strip only when the backlog drained, dot scale moved to the notes,
  larger type (pipeline height 330 → 268 px).
- Type one step larger in every scene on wide screens (15 / 13 / 12 px); diagram box text
  layout no longer depends on font size; timeline ticks thin when labels would touch; paired
  bars spaced for the larger type; diagram labels fall back to the least-overlapping spot and
  group titles take a free corner.
- Not changed: the font (Pretendard cannot be bundled), the 15 CSS-tier cases.

## 0.9.0 — architecture and process diagrams

- New kind `diagram`: components in layers (left to right; top to bottom on phones), typed
  boxes (`person`, `ai`, `data`, `external`), groups over layers, connections with labels,
  two-way pairs as parallel lines, dashed lines with a stated meaning, lanes outside every box
  for connections that skip layers. `data_kind` is `current`, `proposed` or `example` and is
  printed in the picture. Optional `steps` (`path` or parallel `paths`) animate the route a
  request takes; the numbered step list stays in the picture for print, export and no-JS.
- New gate: text that belongs to a box stays inside it; connection labels stay off boxes.
- Recipes now name the kinds that fit them.
- Examples: AI agent request path, RAG indexing, AI adoption approval (15 in total).
- Verification: unit 108; examples 15/15 and live 4/4 under Noto Sans CJK KR and NanumGothic;
  CSS suites pass. Not verified: target Confluence, macOS/Windows fonts, real user content.

## 0.8.0 — more report situations, portable output, second-font gates

- New kind `share` (100% bars: composition and how it changed, highlighted category with its
  %p change; replaces pie charts). `bars` gains `"mode": "funnel"` (conversion and people lost
  per step, overall conversion, `drop: rate|count` because "most drop-off" is ambiguous).
  `timeline` accepts `HH:MM` clock times, `durations`, `legend: false`, `status_labels`,
  `today_label` for incidents.
- Output for places without HTML macros: `figure.svg` (final scene + source line) and
  `figure.png` (2x). Without Playwright/Chromium the build still writes the HTML/SVG and exits
  2 ("BUILT (unchecked)"); exit 1 is reserved for real failures.
- `--font` repeats the gates under another installed font (NanumGothic tested); the font
  stack includes Noto Sans CJK KR. Static kinds print "예시 데이터"/"추정값" in the picture.
- Fixes found by a six-request self-run from the docs and by the final gate runs: milestone
  label rows, x-tick thinning, trend value labels placed in free slots in dot order, node
  name vs capacity label spacing, history strip vs legend spacing, JS/Python rounding
  mismatch (half-up `r1`), a needless "29/29일" counter removed, and the exported SVG's
  source line wrapping instead of running off the figure.
- 12 example specs (added: signup funnel, incident timeline, infra cost share).
- `--check` also gates the exported `figure.svg` (text inside the figure, overlap, painted-over
  text, contrast).
- Verification: unit 107; live 4/4 and examples 12/12 under both fonts (figure gate included);
  CSS suites pass.
  Not verified: target Confluence, macOS/Windows fonts, SVG/PNG in office apps; the
  self-run was not independent.

## 0.7.0 — spec-driven document visuals

The default way to make a visual is now a JSON spec (`references/visual-specs.md`):
`flow`, `trend`, `bars`, `timeline`, built by `scripts/build_visual.py` into a validated
macro (animated or static by situation) and checked by shared browser gates
(`scripts/visual_gates.py`). Three monitoring cases became plain specs of these kinds
(bespoke scenes removed, identical model numbers). Nine report-style examples ship in
`examples/visuals/`; `build_visual_gallery.py` builds a review page. Gates now also catch
transient overlaps (24 moments), text painted over by later shapes, and always check the
final state. Fixes found by review and by an unprepared-spec test: decimals rounded away,
unfilled Hangul placeholders, threshold label under area fill, percent decimals ignored,
event-label collisions, flat changes coloured as wins, timeline note placement, empty
status band, thread-pool overflow counter under dots, stale screenshots, and a drained
backlog invisible in the final picture (single-lane history strip).

## 0.6.1 — readability fixes found in review, with gates

- Caption pacing: `paced_rate()` slows playback so every caption except the last stays on
  screen max(2.5 s, chars / 12) at the default speed; captions rewritten to 25–45 chars;
  build fails when two captions are too close to read (no-queue thread-pool variant merged).
- Contrast: text colours >= 4.5:1 on white (muted 3.32 → 5.02), pill pairs >= 4.5:1; faint
  grey only for non-text. Browser gate checks rendered SVG/HTML text.
- Labels over plotted marks get a white halo; CPU value labels sit above the dot.
- Final/static scene no longer freezes in-flight tokens; buffer occupancy drawn as filled
  cells (1 cell = 1 request), distinct from token dots (1 dot = N requests); waiting is
  always yellow; slot-mode pill moved below the buffer.
- Phone-width static scene (360 px) shown without JavaScript instead of a shrunken 720 px
  one (text was ~6 px); browser gate checks visibility and >= 9 px text.
- Pill widths estimated conservatively; tests now render with Noto Sans CJK KR, which
  exposed and fixed a title/tick collision in thread-pool.

## 0.6.0 — visual language for the live tier

Goal: the look and finish of the kciter.so article demos, not their content. Their
traits were measured from local recordings and applied once in the kit, shell and
grammars: Open Color palette, quiet chrome (no card border, centred status and caption,
text-only controls), waiting requests as dots or buffer cells, stages with a thick gauge
and %, plain-language pills that appear only when true, and charts only where the
article text reads them. `flowQueue` gains a stage-chain variant; `timePanels` gains
sparklines. pipeline-bottleneck drops its queue panel (397 → 260 px at 715 px);
bounded-queue puts the two queues side by side (498 → 340 px); cpu-latency gets
event-timed ①②③ pills; thread-pool keeps its structure and is restyled. Fixed the
browser resize gate, which had passed only because of the old card padding.

## 0.5.0 — pipeline-bottleneck, bounded-queue and cpu-latency on the live tier

`flowQueue` gains a fluid-lane variant for rate models: a queue bar on a request-count
scale, a limit gauge per stage, optional source, dependency and reject branch. Tokens
stand for a fixed number of requests; their arrival, rejection and FIFO departure times
come from the model's cumulative curves, so dots and numbers cannot disagree.
`timePanels` gains column panels and time-array series cut at T.

- pipeline-bottleneck: Gateway → queue → Application → DB in one lane; the main figure
  shows the queue in front of Application and DB's unused capacity. Live line
  "유입 − 처리 = 600 − 300 = 300건/s씩 쌓임". 1,760 → 397 px at 715 px.
- bounded-queue: two lanes on one count scale; the bounded lane diverts rejected tokens.
  Both lanes serve 920 requests, so the scene shows that the cap trades waiting for
  rejection without adding throughput. The old metric cards, which showed final values
  from the start, are gone. 2,283 → 498 px.
- cpu-latency: CPU over P99 per service on one time axis; "연산 포화 의심" and "대기 의심" appear
  only after their events. 3,193 → 347 px.

The runtime test hook is generic (`probe(T)`) and the browser gate runs every live case
against a Python probe. New `tests/compare_baseline.py` makes before/after sheets at
identical model times. Other 15 cases are byte-identical; thread-pool's static scene is
unchanged.

## 0.4.0 — live runtime tier; thread-pool rebuilt on it

Adds a second rendering tier for explanations that must show model state at time T.
Python models stay the single numeric source; `scripts/live_scene.py` bundles a small
JS kit, two reusable grammars (`flowQueue`, `timePanels`), a per-case scene and a runtime
into one self-contained macro with one validated inline script. The static fallback is
the same scene code run in Node at the final time, so export/no-JS show the final scene.

`thread-pool` is the first and only migrated case. Same FIFO model and inputs as v0.3.2.
The diagram now shows the queue, request tokens travel one drawn route into queue and
slots, slow work is visually distinct, active+queued share one stacked panel with the
pool limit, per-request response times share the time axis, and a live line shows
arrival × service time against pool size. Captions and playback pacing bind to model
events. Height at a 715 px container: 1,793 px → 487 px; macro 91 KB → about 50 KB.

Validator accepts scripts only in live roots, only the marked runtime, without
attributes, and without network/storage/dynamic-code/navigation APIs. Gallery re-creates
scripts after mounting (innerHTML never executes them) and passes speed via
`data-ca-speed`; thread-pool gains a before/after toggle. New unit and browser gates.
Other 18 cases and 13 basic patterns are unchanged (CSS tier).


## 0.2.0 — motion expansion and reuse

Added ten patterns: before-after, threshold-cross, recovery, parallel-flow, branch-flow,
approval-gate, retry-loop, request-response, queue-buildup, failure-propagation.
The original three pattern IDs remain, for 13 implemented and 13 planned entries.

A single shared player replaces duplicated controls, styles, reduced-motion and print
handling. Scene sources contain only pattern-specific structure. The generated macro
is still self-contained; source deduplication does not require external CSS in Confluence.
Final macro bytes are larger than the old minimal examples because data tables and
validation-aware labels have been added; no size-reduction claim is made for outputs.

Introduced structured numerical input: line geometry, weighted mean, nearest-rank P95
and queue conservation are computed rather than independently editable labels. Normal
strings are HTML-escaped; invalid/unknown inputs fail. Added stricter CSS/HTML lint and
actual unit/browser tests. Default playback is once, then the final state is retained.

Gallery data is generated by the production renderer, not hand-copied demo markup.
Search and categories select a single rendered preview. The gallery source is
`gallery/index.html`; run the builder to produce standalone `dist/gallery.html`.

Compatibility: legacy text-template helper remains, but old `--set` motion commands
now fail with explicit guidance to structured inputs. Existing generated v0.1 HTML
fragments are not remotely modified. Source scenes must be assembled before publishing.

Original eight document recipes and general authoring scope are preserved. Weekly
reporting remains one optional recipe, not the library's default document format.
