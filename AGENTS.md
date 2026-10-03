# Repository work rules

Read SKILL.md and docs/STATUS.md first. Inspect current main, working branch and PR;
reuse the existing change instead of rebuilding completed work. Preserve unrelated
recipes, user content and files. Do not force-push, merge, release or publish Confluence
pages unless explicitly requested. New changes go on the current review branch.

Basic motion source is player.* + selected scene + typed input + scripts/motion.py.
Monitoring reference cases also use scripts/monitoring_cases.py and reference_scene.py.
Generated gallery/macros come from that renderer; never hand-maintain a second demo
implementation. Do not count planned catalog entries as implemented.

Document visuals (v0.7.0+): new visuals go through the spec path (references/visual-specs.md,
scripts/build_visual.py --check, examples/visuals/). Do not hand-write a scene a kind can express;
extend the kind instead, with tests (tests/test_visual_spec.py) and the shared gates (scripts/visual_gates.py).

Live runtime (v0.4.0+): cases marked `"runtime": "live"` render model state at time T with
one bundled inline script (scripts/live_scene.py + visuals/live/). Read
references/live-runtime.md before touching them. Numbers come from the Python model only;
captions and pacing bind to model events; the static fallback is the same JS scene run in
Node. Do not hand-edit generated macros, add other scripts, or migrate a case without
its unit and browser gates (tests/test_live_runtime.py, tests/browser_live.py). Migrated:
thread-pool (custom scene), pipeline-bottleneck, bounded-queue, cpu-latency, slow-degradation,
postmortem-timeline (specs of flow/trend); do not claim others are. Each migration is checked
side by side with the article demo (dist/ref18/pairs, local only, not committed).

Read references/diagram-layout.md for structure/flow work. Explicit route coordinates
must generate both the visible line and particle motion. The current layout pass covers
cascade, event loop and pipeline only; do not claim all cases have been redesigned.
Preserve previous mechanism changes and the 1.25x default. Run geometry and browser
checks before considering a layout complete.

Run unit tests, build the gallery, and run browser tests when available. Record actual
commands, environment and failures. Never report browser/Confluence verification
from static lint alone. Update docs/STATUS.md and PR verification from real results.
Keep generated dist outputs, real content, secrets and font files out of Git history.
