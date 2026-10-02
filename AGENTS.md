# Repository work rules

Read SKILL.md and docs/STATUS.md first. Inspect current main, working branch and PR;
reuse the existing change instead of rebuilding completed work. Preserve unrelated
recipes, user content and files. Do not force-push, merge, release or publish Confluence
pages unless explicitly requested. New changes go on the current review branch.

Motion source is player.* + selected scene + typed input + scripts/motion.py.
Generated gallery/macros come from that renderer; never hand-maintain a second demo
implementation. Do not count planned catalog entries as implemented.

Run unit tests, build the gallery, and run browser tests when available. Record actual
commands, environment and failures. Never report browser/Confluence verification
from static lint alone. Update docs/STATUS.md and PR verification from real results.
Keep generated dist outputs, real content, secrets and font files out of Git history.
