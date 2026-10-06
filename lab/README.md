# lab — reference material, not the product

The skill an author (person or in-house AI) uses is the spec path at the repository root: `SKILL.md`,
`references/visual-specs.md`, `examples/visuals/`, `scripts/build_visual.py`. Nothing there imports this folder.

This folder keeps what the product was measured and built against:

| What | Where (relative to `lab/`) |
|---|---|
| The 18 cases of the kciter.so monitoring article (+ gc-pause bonus), rebuilt as live scenes, and their CSS predecessors | `scripts/monitoring_cases.py`, `reference_scene.py`, `mechanism_scenes.py`, `diagram_scenes.py`, `diagram_layout.py`, `build_monitoring_suite.py`, `examples/monitoring-cases.json`, `references/monitoring-*.md`, `layout-quality-review.md` |
| The 13 CSS motion patterns (v0.1-0.3, for a Confluence that cannot run inline scripts) | `scripts/motion.py`, `render_motion.py`, `render_template.py`, `build_gallery.py`, `visuals/`, `examples/motion-inputs.json`, `references/motion-*`, `gallery/` |
| Their tests, including the browser runs of the live runtime over the 18 cases | `tests/` |

Paths inside this folder's documents are relative to `lab/`. Modules here import the product modules from
`../scripts` (model, live_scene, visual_spec, choreo); the product never imports `lab`. The live scenes the cases use
stay in `visuals/live/` because they are the shared runtime (thread-pool is the worked example of a custom scene).
Build outputs go to `lab/dist/` (ignored by git).

    python -m unittest discover -s lab/tests
    python lab/scripts/build_monitoring_suite.py
    python lab/tests/browser_live.py                        # live runtime, 18 cases, in Chromium
    python lab/scripts/build_gallery.py && python lab/tests/browser_smoke.py
