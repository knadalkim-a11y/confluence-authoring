# Repository work rules

Read SKILL.md and docs/STATUS.md first. Inspect current main, working branch and PR;
reuse the existing change instead of rebuilding completed work. Preserve unrelated
recipes, user content and files. Do not force-push, merge, release or publish Confluence
pages unless explicitly requested. New changes go on the current review branch.

## Layout of the repository

- Product (what an author or in-house AI uses): SKILL.md, references/, recipes/, templates/,
  examples/visuals/ (copyable specs), scripts/ (build_visual.py entry; visual_spec.py -> kinds/<kind>.py;
  model.py shared numbers and caption pacing; choreo.py cues; live_scene.py bundling and the Node static render;
  visual_gates.py browser gates; figure_metrics.py clutter numbers), visuals/live/ (kit, choreo, grammars,
  scenes, runtime), tests/ (unit tests and frozen fixtures).
- lab/ (reference material, see lab/README.md): the 18 monitoring-article cases + gc-pause bonus the engine was
  measured against, and the v0.1-0.3 CSS motion patterns, with their tests. lab imports product modules; the
  product never imports lab. Do not count planned catalog entries in lab as implemented.

## Visuals

New visuals go through the spec path (references/visual-specs.md, scripts/build_visual.py --check,
examples/visuals/). Do not hand-write a scene a kind can express. For new ideas extend the compose engine
(a container, part or routing rule that works everywhere), never one figure; extend the kind with tests
(tests/test_visual_spec.py) and the shared gates (scripts/visual_gates.py). Concept forms are compose presets;
diagram keeps its own tuned scene (visuals/live/scenes/diagram.js) because moving it onto compose made figures busier.

Live runtime: one bundled inline script per macro (scripts/live_scene.py + visuals/live/); read
references/live-runtime.md first. Numbers come from the Python model only; captions and pacing bind to model
events; the static fallback is the same JS scene run in Node. Do not hand-edit generated macros or add other
scripts. Moving dots are K.token at the kit pace, connectors K.wire(K.ortho(...)), data-riding markers K.follow;
state changes are cues from the kind (choreo), never a one-frame switch in scene code. Fix a pace or routing
problem in the kit or the kind, never in one case; visual_gates.MOTION_JS enforces it. Preserve the 1.25x default.
visuals/live/*.js changed by hand keep their style; compose.js follows visuals/live/.prettierrc.json.

Step targets: each captioned step is about one part; the engine lights it while the step is current. Steps
name parts by author ids only. Nothing numbered is drawn on the picture (the user rejected badges in 0.19.0).

## Accepting changes

- A refactor must not change output: compare data and frames (3 widths x 5 times) of every example, the local
  evaluation sets and the lab cases before and after, plus macros when no JS was reformatted.
- A layout or routing change is accepted only when scripts/figure_metrics.py on the built figures (examples and
  the local evaluation sets) is not busier than the previous revision (bends, crossings, length, near misses) and a
  side-by-side shows no figure got worse; gates passing is not enough. The metrics do not see decorations
  (badges, labels): judge those by eye. Show the side-by-side to the user before committing a visible change.
- Reproduce in-house feedback with fictional content (internal data never leaves the company) and keep the
  reproduction as a fixture in tests/fixtures/.

Run unit tests (tests/ and lab/tests/), build the gallery, and run browser tests when available
(build_visual.py --check on the examples, lab/tests/browser_live.py for the runtime, both with a second Korean
font). Record actual commands, environment and failures. Never report browser/Confluence verification
from static lint alone. Update docs/STATUS.md and PR verification from real results.
Keep generated dist outputs, real content, secrets and font files out of Git history.
