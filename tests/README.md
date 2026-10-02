# Validation

Run from repository root:

```sh
python -m unittest discover -s tests -v
python scripts/build_gallery.py
python tests/browser_smoke.py --browser /path/to/chromium
```

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
