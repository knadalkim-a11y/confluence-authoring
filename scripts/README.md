# Scripts (the spec path)

`build_visual.py SPEC.json --out DIR [--check] [--font FAMILY] [--phone] [--browser PATH]` builds one
document visual from a JSON spec into `DIR/macro.html`, `preview.html`, `figure.svg` (final scene with a source
line), `figure.png` (2x, when Chromium starts) and `report.json` (layout decisions, clutter numbers, step -> part
correspondence). `--check` runs the shared browser gates and writes screenshots to `DIR/shots/`; `--font` repeats
them under another installed font. Exit 0 = pass, 1 = spec/lint/gate failure, 2 = built but the gates could not
run (no Playwright or Chromium). See references/visual-specs.md.

`build_visual_gallery.py SPEC_DIR --out DIR [--check]` builds every spec in a folder into one review page.

| Module | Role |
|---|---|
| `visual_spec.py` | entry: `build(spec)` dispatches to the kind; public names (`SpecError`, `fluid_schedule`, ...) |
| `kinds/common.py` | spec errors, field checks, number formatting, caption binding, the common header |
| `kinds/<kind>.py` | one per kind: flow, trend, bars, share, timeline, diagram, distribution, compose, concept |
| `model.py` | shared numbers: statistics, series, token streams, caption reading time and pacing |
| `choreo.py` | cues (on, act, level, pop, reveal) and their validation; `visuals/live/choreo.js` plays them |
| `live_scene.py` | bundles kit + choreo + grammars + scene + runtime into one macro; runs the same scene in Node for the static SVG |
| `visual_gates.py` | browser gates (overlap, cover, contrast, boxes, layout, motion, height) |
| `figure_metrics.py` | clutter numbers (wires, bends, crossings, length, near misses) to compare revisions |
| `validate_html_macro.py` | static lint of a fragment (ids, prefixes, external resources, unsafe tags); not a sanitizer |

Building needs Python 3.10+ and Node.js; no third-party Python packages. No command logs into GitHub or
Confluence or performs a remote write. The reference-case and CSS-pattern tools are in `lab/scripts/`.
