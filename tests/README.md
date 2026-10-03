# Validation

Run from repository root:

```sh
python -m unittest discover -s tests -v
python scripts/build_gallery.py
python tests/browser_smoke.py --browser /path/to/chromium
python scripts/build_monitoring_suite.py && python tests/browser_monitoring.py
python tests/browser_live.py [--browser /path/to/chromium]
python tests/compare_baseline.py --baseline <previous build dir>   # before/after sheets
```

`browser_live.py` runs live-runtime cases with JavaScript enabled: autoplay, height
budget, text overlap at fixed model times and widths, browser state equal to the Python
model (per-case probes from `monitoring_cases.live_checks`), event-bound captions, no
future annotations, controls, resize, print, reduced motion, no-JS static scene, two
instances and gallery execution. `compare_baseline.py` captures a previous build and the
current one at the same model times and widths (CSS tier via its 6–86% wall mapping) into
side-by-side sheets for human review; it judges nothing. `browser_monitoring.py`
keeps JavaScript disabled and skips live cases.

The first two commands use only Python's standard library. Browser smoke tests need
Playwright and an installed Chromium executable. The `--browser` argument avoids
requiring a separate Playwright browser download. Do not bypass browser security
policies. Tests render our generated HTML with `set_content`, without navigating to
external pages. Macro page JavaScript is disabled; test instrumentation samples CSS
states using the Web Animations API in a separate step from untouched CSS-control tests.

Verification layers are deliberately separate:
- Unit tests: input validation, escaped text, numerical correctness, catalog paths,
  repeat/prefix rules, CSS/HTML lint, combined-block isolation and build parity.
- Browser tests: running clocks, distinct visual states, pause/resume/replay, static
  final state equality, 390px layout, keyboard, reduced motion, print, gallery search,
  filtering, single active preview and no external requests.
- Manual visual review: wide and narrow screenshots of the generated examples.
- Target Confluence: **not performed**. Saving content and checking animation in the
  target page remain independent tasks. These tests do not connect to Confluence.

`browser-report.json` is actual browser output. `verification.json` records commands,
unit count and source fingerprints. Treat these as version-specific snapshots, not
proof for later modified content. Semantic authoring scenarios in `test-cases.md`
remain evaluation criteria; there is no automatic LLM evaluation in this package.
