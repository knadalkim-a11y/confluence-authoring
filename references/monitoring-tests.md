# Monitoring reference tests

The pack has 30 numerical/input/render test methods and 19 browser-tested cases.
Historical v0.2 test evidence is preserved separately; it was not all rerun here.
No original-site live A/B, Confluence publishing, CI run or FPS equivalence is claimed.

## Build and unit checks

Python 3.10+; rendering and unit tests use the standard library only.

```sh
python -m compileall -q scripts tests
python -m unittest discover -s tests -p test_monitoring_suite.py -v
python scripts/build_monitoring_suite.py
```

## Actual browser checks

Install Playwright and Pillow in the test environment, not in Confluence. The recorded
run used Python 3.13.5, Playwright 1.57.0, Pillow 12.3.0 and Chromium 144.0.7559.96.
The script currently expects Chromium at /usr/bin/chromium; change that one executable
path to the installed browser for another test environment. Browser dependencies are
not needed to view the generated HTML.

```sh
python tests/browser_monitoring.py --start 0 --count 10 --skip-extra
python tests/browser_monitoring.py --start 10 --count 9 --skip-extra
python tests/browser_monitoring.py --extra-only
python tests/merge_monitoring_reports.py
```

Shards avoid the execution tool timeout; they are not partial coverage. The merger
requires all 19 cases exactly once, matching test SHA and current artifact SHA256.
The full combined result is dist/monitoring-suite/browser-report.json. The committed
tests/monitoring-browser-report.json compactly records the same case results and hashes.
Screenshots and original shard reports are generated under dist/ and are not committed.

Case checks include advancing clocks, intermediate visual changes, pause/resume/replay,
static-final equivalence, 320/390px and narrow-container layout, reduced motion and print.
Extra checks cover independent instances, keyboard focus, event-loop rotation actually
stopping, eight occupied worker slots at model 5s, all gallery selections and filters,
exact macro code view, one active preview, and no external requests/script errors.

Static lint is not a security sanitizer; test instrumentation is not macro JavaScript.
An animated property changing at intermediate times is not an FPS benchmark.

## Measurement and provenance

See tests/monitoring-verification.json for source blob hashes, counts and optimization.
The byte comparison uses identical final inputs and prefixes with/without redundant
collinear-keyframe removal; it does not compare different versions or remove data.
The baseline player and validator were retrieved through the authorized connector.
Source-snapshot testing was used because the container could not resolve github.com.

## Regressions fixed during this work

Mean mismatch, GC-time mismatch, consecutive worker-slot false-idle, number overlap,
failure-path disappearance and premature failed DB styling were fixed and retested.
Contact-sheet generation skips screenshots belonging to later, not-yet-run shards.
