# Local generation tools

`render_motion.py PATTERN OUTPUT --input INPUT.json [--prefix PREFIX] [--preview FILE]`
assembles one typed motion instance. Use `--example` instead of `--input` only for an
explicitly illustrative demo. The output is a copy-ready macro fragment; the optional
preview adds document-level wrappers that must not be pasted into an HTML macro.

`build_gallery.py [--output DIRECTORY]` renders every implemented example with the same
renderer, checks each fragment and generates a standalone search/filter gallery,
individual previews, macro fragments, input JSON files and a byte-size manifest.

`validate_html_macro.py FILE` lints rendered fragments, including multiple combined
blocks: duplicate IDs/prefixes/keyframes, unscoped CSS, undefined animation names,
broken ID references, unresolved tokens, external runtime resources, unsafe tags or
event attributes, and required reduced-motion/print fallbacks. This is not a sanitizer.

`render_template.py TEMPLATE OUTPUT --prefix PREFIX --set KEY=value` remains an escaped
text-template helper for ordinary templates. v0.2 scene sources require typed input via
render_motion.py; the legacy command fails with migration guidance rather than silently
relabeling fixed numerical geometry. Do not use --allow-unresolved output for publishing.

`build_visual.py SPEC.json --out DIR [--check] [--font FAMILY] [--browser PATH]` builds one
document visual from a JSON spec (`visual_spec.py`: validation, models, events, placeholders,
pacing) into `DIR/macro.html`, `preview.html`, `figure.svg` (final scene with a source line),
`figure.png` (2x, when Chromium starts) and `report.json`; `--check` runs the shared browser
gates (`visual_gates.py`, including the exported figure) and writes screenshots to
`DIR/shots/` (cleared each run); `--font`
repeats the gates under another installed font. Exit 0 = pass, 1 = spec/lint/gate failure,
2 = built but the gates could not run (no Playwright or Chromium). See references/visual-specs.md.
`build_visual_gallery.py SPEC_DIR --out DIR [--check]` builds every spec in a folder into one
review page (`DIR/index.html`) that embeds each macro.

`live_scene.py` (library, used by `build_visual.py` and `build_monitoring_suite.py`) assembles live-runtime
cases: model data from `monitoring_cases.py`, JS kit/grammars/scene/runtime from
`visuals/live/`, and a static final-scene SVG rendered by running the same scene code
in Node. Only cases marked `"runtime": "live"` use it. See references/live-runtime.md.

Generation requires Python 3.10+ and no third-party packages (live cases also need Node.js). Catalog is serialized as
JSON-compatible YAML (YAML 1.2 subset), so standard-library json.load can read it.
No generation command logs into GitHub or Confluence or performs a remote write.
