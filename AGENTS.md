# Repository work rules

Read SKILL.md and docs/STATUS.md first. Inspect current main, working branch and PR;
reuse the existing change instead of rebuilding completed work. Preserve unrelated
recipes, user content and files. Do not force-push, merge, release or publish Confluence
pages unless explicitly requested. New changes go on the current review branch.

Basic motion source is player.* + selected scene + typed input + scripts/motion.py.
Monitoring reference cases also use scripts/monitoring_cases.py and reference_scene.py.
Generated gallery/macros come from that renderer; never hand-maintain a second demo
implementation. Do not count planned catalog entries as implemented.

Read references/diagram-layout.md for structure/flow work. Explicit route coordinates
must generate both the visible line and particle motion. The current layout pass covers
cascade, event loop and pipeline only; do not claim all cases have been redesigned.
Preserve previous mechanism changes and the 1.25x default. Run geometry and browser
checks before considering a layout complete.

Run unit tests, build the gallery, and run browser tests when available. Record actual
commands, environment and failures. Never report browser/Confluence verification
from static lint alone. Update docs/STATUS.md and PR verification from real results.
Keep generated dist outputs, real content, secrets and font files out of Git history.
