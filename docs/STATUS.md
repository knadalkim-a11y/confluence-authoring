# Status — v0.5.0 three more cases on the live tier

Review branch: `feat/initial-authoring-skill`, existing Draft PR #1 (pushed v0.4.0 `771f480` first).
No main merge, Draft removal, release, permission change or Confluence publication.

## Changed

- `pipeline-bottleneck`, `bounded-queue` → `flowQueue` fluid lane (new variant of the same
  grammar: queue bar on a request-count scale, stage limit gauges, optional source,
  dependency and reject branch, tokens = `unit` requests from the model's cumulative
  curves). Same `fluid_queue` model and inputs as before.
- `cpu-latency` → `timePanels` (`panelIn`, `series`): per service, CPU above P99 on one
  time axis; verdicts appear only after the knot event that justifies them. Scenario
  curves moved to `cpu_scenarios()`, shared by the CSS builder and the live scene.
- Runtime: `stats.right` optional; test hook `state()` now returns the scene's `probe(T)`.
  Thread-pool static scene and status line are byte-identical to v0.4.0 (its macro bytes
  differ only because the bundled kit/grammars grew).
- `tests/browser_live.py` is case-generic via `monitoring_cases.live_checks()` (Python
  probe, sample times, event-bound annotations). New `tests/compare_baseline.py` makes
  before/after sheets at identical model times and widths. `--baseline` now gives the
  gallery toggle to every live case plus the two layout revisions.
- CSS builders for the three cases are kept (still unit-tested via `runtime: "css"`);
  `browser_diagram_layout.py` no longer covers pipeline-bottleneck. Browser tests fall back
  to Playwright's Chromium when `/usr/bin/chromium` is absent.
- Other 15 monitoring macros: byte-identical to the v0.4.0 build.

## Actual validation (this environment: Linux, Python 3.11, Node 22, Playwright 1.56 + Chromium 141)

- Unit: 90 tests pass (85 prior + 5 new; 3 prior tests re-pointed to CSS cases).
- `tests/browser_live.py`: all 4 live cases pass every gate. Heights (715 / 360 px):
  thread-pool 487 / 504, pipeline-bottleneck 397 / 409, bounded-queue 498 / 533,
  cpu-latency 347 / 587. Report: `tests/live-browser-report.json`.
- `tests/browser_monitoring.py` (15 CSS cases + gallery), `tests/browser_smoke.py`
  (13 basic patterns), `tests/browser_diagram_layout.py` (2 layout cases): pass. Their
  committed reports were not regenerated.
- Before/after sheets (`tests/compare_baseline.py --baseline <v0.4.0 build>`) were looked
  at by the agent, not by a person. Heights at 715 px: pipeline 1,760 → 397,
  bounded 2,283 → 498, cpu 3,193 → 347.

## Known limits (stated, not hidden)

- The fluid model integrates in 0.05 s steps; the bounded queue fills at 4.10 s in the
  model vs 4.08 s in closed form. Captions use the model value.
- cpu-latency's 60 s axis is a synthetic reading aid (the source has no time unit).
- bounded-queue at 715 px is 498 px of a 520 px budget; little room for more content.
- In pipeline-bottleneck the outgoing token stream to DB is short (one or two dots on a
  52 px connector); readable but not reviewed by a person.

## Boundaries

Target Confluence: inline-script execution, CSP, editor view, mobile apps and PDF export
are NOT verified; run the smoke check in `references/confluence-rules.md` first. Aesthetic
quality is a human judgement; gates only catch mechanical defects.
