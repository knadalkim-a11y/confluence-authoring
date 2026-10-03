# Status — v0.4.0 live runtime tier

Review branch: `feat/initial-authoring-skill`, existing Draft PR #1.
Starting point: `5783eb58d816863246dbc523e41cf34b1fda85a5` (v0.3.2), no later remote commits found.
No main merge, Draft removal, release, permission change or Confluence publication.

## Changed

- New live tier: `scripts/live_scene.py`, `visuals/live/` (kit, grammars `flowQueue` and
  `timePanels`, scene `thread-pool`, runtime, shell). Architecture, composition rules and
  gates: `references/live-runtime.md`.
- `thread-pool` migrated (`"runtime": "live"`). Same `pool_model` inputs and numbers as
  v0.3.2; captions and pacing bound to model events (queue onset 4.2 s, peak 14 at 8.85 s,
  drain 10.05 s). The v0.3.2 diagram matched the model at exact times but did not show
  the queue; v0.4.0 shows queue, slow work and arrival × service time in the main figure.
- Validator, gallery (script mounting, speed, before/after for thread-pool), suite tests,
  CSS browser test (skips live cases; no hard-coded browser path), docs.
- Other 18 monitoring macros: byte-identical to a v0.3.2 build at the same prefix/speed.

## Actual validation (this environment: Linux, Python 3.12, Node 22, Playwright Chromium)

- Unit: 85 tests pass (74 prior + 11 live).
- `tests/browser_live.py`: thread-pool passes all gates — height 487 px at 715 px and
  504 px at 360 px, no text overlap/clipping at 6 model times × 2 widths, browser state and
  status numbers equal Python `pool_state`, captions on events, no future annotations,
  controls/keyboard, resize, print, reduced motion, no-JS static scene, two instances,
  gallery execution, no errors or external requests. Report: `tests/live-browser-report.json`.
- `tests/browser_monitoring.py` (18 CSS cases + gallery incl. live mount), `browser_smoke.py`
  (13 basic patterns) and `browser_diagram_layout.py`: pass. Their committed reports were
  not regenerated in this change.
- Before/after at identical model times and width was reviewed by screenshot.

## Boundaries

Target Confluence: inline-script execution, CSP, editor view, mobile apps and PDF export
are NOT verified; run the smoke check in `references/confluence-rules.md` first. Aesthetic
quality is a human judgement; gates only catch mechanical defects. Only thread-pool uses
the live tier; the grammar mapping for other cases in live-runtime.md is a plan.
