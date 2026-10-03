# Status — v0.6.0 visual language for the live tier

Review branch: `feat/initial-authoring-skill`, Draft PR #1. No main merge, Draft removal,
release or Confluence publication.

## Goal of this change

Reach the look, feel and finish of the kciter.so article demos (not their content). The
originals were recorded locally (canvas pixels, ~45 s per demo, 673 px column) and their
traits measured; the result is a shared visual language in
`references/visual-guidelines.md` → "Visual language (live tier, v0.6.0)".

## Changed

- `kit.js`: Open Color palette with legible text variants; `rich`, `pill`, `gauge`, `ring`,
  `arrow`, `tw` helpers.
- `shell.html`: no card border; centred status line joined by " · "; centred grey caption;
  notes and text-only controls on one low row.
- `flowQueue`: stage-chain variant (`chainGeom/chainDraw`) replaces the v0.5.0 bar lane:
  stage limit + thick gauge + %, pills, dot-grid queue or buffer slots, reject tokens.
  Pool variant (thread-pool): waiting requests yellow, busy slots solid blue, DB green/red.
- `timePanels`: `spark`; lighter cursor; last x tick right-aligned; slow band red family.
- pipeline-bottleneck: queue panel removed (the article text never reads it); 397 → 260 px.
- bounded-queue: lanes side by side (stacked < 560 px), buffer of 8 cells, per-lane
  readouts (대기, 대기 시간, 처리, 거부) and wait-time sparkline; 498 → 340 px.
- cpu-latency: ①②③ pills whose names appear at their events, light panels, value at the
  cursor dot, per-column reading at its event; 347 → 356 px.
- thread-pool: same structure and charts (the article text refers to both), restyled.
- Tests: browser resize gate fixed (it compared a fixed-width container and only passed
  by accident of padding); static-scene text threshold made case-generic (≥ 8).

## Actual validation (Linux, Python 3.11, Node 22, Playwright 1.56 + Chromium 141)

- Unit: 90 pass. `tests/browser_live.py`: 4/4 live cases pass all gates. Heights
  (715 / 360 px): thread-pool 472 / 453, pipeline 260 / 254, bounded 340 / 560, cpu 356 / 548.
- `browser_monitoring.py` (15 CSS cases), `browser_smoke.py`, `browser_diagram_layout.py`: pass.
- Other 15 monitoring macros byte-identical to v0.5.0.
- Before/after: `tests/compare_baseline.py --baseline <v0.5.0 build>`. Original vs ours:
  local page `dist/compare-original/index.html` (article text and recordings are
  third-party content; kept out of Git). Both were reviewed by the agent, not by a person.

## Known limits

- "Feel" is a human judgement; the gates only catch mechanical defects.
- bounded-queue at 360 px is 560 px (budget 600); it grew from 533.
- pipeline's outgoing token stream between Application and DB shows 1–2 dots.
- The status line can wrap at 360 px and then begins its second line with "·".
- Target Confluence: inline scripts, CSP, editor, mobile, PDF export NOT verified.
