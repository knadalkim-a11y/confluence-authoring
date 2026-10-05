# Repository work rules

Read SKILL.md and docs/STATUS.md first. Inspect current main, working branch and PR;
reuse the existing change instead of rebuilding completed work. Preserve unrelated
recipes, user content and files. Do not force-push, merge, release or publish Confluence
pages unless explicitly requested. New changes go on the current review branch.

Basic motion source is player.* + selected scene + typed input + scripts/motion.py.
Monitoring reference cases also use scripts/monitoring_cases.py and reference_scene.py.
Generated gallery/macros come from that renderer; never hand-maintain a second demo
implementation. Do not count planned catalog entries as implemented.

Document visuals (v0.7.0+; concept kind v0.15.0 for compare/stack/sequence ideas): new visuals go through the spec path (references/visual-specs.md,
scripts/build_visual.py --check, examples/visuals/). Do not hand-write a scene a kind can express;
extend the kind instead, with tests (tests/test_visual_spec.py) and the shared gates (scripts/visual_gates.py).

Live runtime (v0.4.0+): cases marked `"runtime": "live"` render model state at time T with
one bundled inline script (scripts/live_scene.py + visuals/live/). Read
references/live-runtime.md before touching them. Numbers come from the Python model only;
captions and pacing bind to model events; the static fallback is the same JS scene run in
Node. Do not hand-edit generated macros, add other scripts, or migrate a case without
its unit and browser gates (tests/test_live_runtime.py, tests/browser_live.py). Migrated:
all 18 article cases: thread-pool, cpu-throttling, cluster-cascade, event-loop, timeout-mismatch
(custom scenes); pipeline-bottleneck, bounded-queue (flow); cpu-latency, slow-degradation,
postmortem-timeline, traffic-patterns, survivorship-bias, memory-leak, memory-spike,
utilization-wait, cache-stampede, deploy-comparison (trend); percentile-comparison
(distribution). gc-pause (bonus) stays on the CSS tier; do not claim it is migrated. Each migration is checked
side by side with the article demo (dist/ref18/pairs, local only, not committed).

Motion and wiring (v0.11.0+): moving dots are K.token at the kit pace (K.M), connectors are
K.wire(K.ortho(...)), data-riding markers K.follow. State changes are cues from the kind (scripts/choreo.py + visuals/live/choreo.js,
migrated: diagram, trend, flow, cascade, thread-pool; durations in on-screen seconds), never a one-frame
switch in scene code. Fix a pace or routing problem in the kit or
the kind, never in one case; visual_gates.MOTION_JS enforces it for every live visual.

Read references/diagram-layout.md for structure/flow work. Explicit route coordinates
must generate both the visible line and particle motion. The CSS layout pass (cascade, event
loop, pipeline) is retired: those cases are live scenes now, gated by tests/browser_live.py, and
tests/browser_diagram_layout.py reports SKIP while no CSS layout case remains.
Preserve previous mechanism changes and the 1.25x default. Run geometry and browser
checks before considering a layout complete.

Run unit tests, build the gallery, and run browser tests when available. Record actual
commands, environment and failures. Never report browser/Confluence verification
from static lint alone. Update docs/STATUS.md and PR verification from real results.
Keep generated dist outputs, real content, secrets and font files out of Git history.
