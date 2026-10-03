# Live runtime — architecture, contract and quality gates (v0.4.0)

The CSS-keyframe renderer (`reference_scene.py`) bakes every movement into keyframes.
That made state-driven pictures hard: decorative token streams needed disclaimers,
fixed `0.9`-style caption times could run ahead of the model, and one generic shell
(panels + metric cards + small line charts + numbered phase boxes) made every case look
alike. The live runtime renders the model state at time T instead.

Use it only where the target Confluence executes inline scripts in HTML macros
(see confluence-rules.md). The CSS tier remains for the other 18 cases and the 13
basic patterns until each is migrated; a case uses exactly one tier at a time.

## Layers

| Layer | Location | Responsibility |
|---|---|---|
| Model | `scripts/monitoring_cases.py` (Python) | Deterministic numbers, event table, derived events (queue onset, peak, drain). Unit-tested. |
| Scene data | `*_live_data()` in the same module | Captions and playback pacing bound to model events; axes; labels. Text numbers are computed, never typed. |
| Grammar | `visuals/live/grammars/*.js` | Reusable pure `draw` functions returning SVG strings for one visual idea, with wide and narrow geometry. No DOM. |
| Scene | `visuals/live/scenes/<case>.js` | Maps model state at T to grammar inputs; status-line numbers. No numbers of its own. |
| Kit | `visuals/live/kit.js` | SVG string helpers and palette. |
| Runtime | `visuals/live/runtime.js` | Clock, rate map, controls, reduced motion, visibility, resize, print, test hooks. |
| Assembler | `scripts/live_scene.py` | Bundles kit+grammars+scene+runtime+data into one `<section>`; renders the static fallback by running the same scene code in Node at the final time. |

Implemented grammars: `flowQueue` (inflow → FIFO queue → worker pool → dependency) and
`timePanels` (panels sharing one model-time axis: band, stacked area, limit line,
points, cursor). Implemented scenes: `thread-pool`.

Candidate grammar mapping for the remaining cases (planning, not implemented):
flow+queue — pipeline-bottleneck, bounded-queue; shared-time panels — cpu-latency,
memory-leak, memory-spike, slow-degradation, deploy-comparison, gc-pause, traffic,
survivorship; distribution dots — percentile; topology fan-out — cluster-cascade;
cycle — event-loop; time-budget bars — cpu-throttling, timeout-mismatch, postmortem;
function curve with moving point — utilization-wait; flow+panels — cache-stampede.

## Fragment contract

- One `<section class="PREFIX" data-ca-prefix="PREFIX" data-ca-runtime="live">` per block,
  containing scoped `<style>`, a status line, `<svg data-ca-live data-ca-static>` that
  already holds the final scene, caption, controls, one `<details>` with model notes and
  the event table, and exactly one attribute-less inline `<script>`.
- The script starts with `/*ca-live-runtime v1*/`, locates its root by prefix, and uses
  no network, storage, dynamic code, navigation or cross-frame APIs (validator-enforced).
  Data is serialized with `<`, `>`, `&`, U+2028/2029 escaped.
- Without JavaScript (PDF/Word export, sanitized macro, disabled scripts) the reader sees
  the final scene, final status line and final caption; controls stay hidden.
- Plays once when first visible, keeps the final scene; replay/pause/final are buttons.
  Reduced motion shows the final scene without autoplay. `beforeprint` shows the final scene.
- `data-ca-speed` multiplies the scene's rate map (gallery speed selector edits it).

## Composition rules (why the thread-pool rebuild works)

1. The main figure carries the core state. If a chart shows something the diagram
   does not (queue length, which work is slow), redesign the diagram.
2. One claim per scene; captions state that claim and change only when the model event
   that makes it true has happened (`captions[i][0]` = event time).
3. Show each number once, at the place the eye already is. Prefer a live causal line
   (e.g. "6.7건/s × 2.0초 = 13.3칸 > 8") over a row of KPI cards.
4. Annotations appear only at or after the time they describe. Never draw future
   values (peaks, maxima) before the clock reaches them.
5. Provenance, assumptions and raw tables go in one collapsed `<details>`, not in the
   picture. The picture still says what is modelled through axis titles and units.
6. Height budget: ≤ 520 px at a 715 px container, ≤ 600 px at 360 px. If it does not fit,
   cut redundant panels before shrinking type below 11 px.
7. Pace in model time, play in wall time: slow the transition into the incident, move
   faster through tails, never skip the moment the claim becomes visible.
8. Moving tokens follow the same straight route that is drawn; tokens represent
   requests, not decoration.

## Quality gates

`tests/test_live_runtime.py` (unit): model binding to `pool_model`, captions on events,
no-queue variant, static fallback equals the Node render of the same code, inert data,
validator rejects foreign/modified scripts, determinism, two-instance isolation.

`tests/browser_live.py` (Chromium, JS on): autoplay, height budget at 715/360 px, no
horizontal overflow, no SVG text overlap or clipping at six model times and two widths,
browser state and status numbers equal Python `pool_state(T)`, caption equals the
event-bound caption, no future annotation leak, controls and keyboard, resize keeps the
clock, print/reduced-motion final scene, independent instances, no errors or external
requests, no-JS static scene, gallery executes the macro. Writes screenshots at fixed
model times for human review.

These gates do not judge aesthetics. A before/after sheet at identical model times and
widths still needs a human look.

## Adding a live case

1. Keep or write the Python model; add `<case>_live_data(params)` returning
   `(data, aria, notes, table, numeric)`, with captions/pacing bound to model events.
2. Reuse a grammar; add a new one only for a genuinely new visual idea, as a pure
   `draw` with wide and narrow geometry.
3. Add `visuals/live/scenes/<case>.js`; register in `LIVE_BUILDERS`; add
   `"runtime": "live"` to the case in `examples/monitoring-cases.json`.
4. Extend the unit and browser gates for the case's own invariants; build the suite with
   `--baseline` and compare screenshots at the same model times and widths.
5. Remove nothing from the CSS builder until the live case passes; then the CSS
   builder for that case may be deleted in a later change.

## Not verified

Target Confluence script execution, CSP, editor/preview behavior, mobile apps and
PDF export of a real page. Run the smoke check in confluence-rules.md first.
