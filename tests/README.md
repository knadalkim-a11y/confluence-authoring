# Validation

Run from the repository root:

```sh
python -m unittest discover -s tests          # spec path (kinds, model, choreo, fixtures)
python -m unittest discover -s lab/tests      # reference cases, live runtime, CSS patterns
for f in examples/visuals/*.json; do python scripts/build_visual.py "$f" --out dist/visuals/$(basename "$f" .json) --check; done
# repeat with --font NanumGothic (any installed Korean font) to catch metric-dependent overlaps
python lab/tests/browser_live.py [--font NanumGothic --output lab/dist/live-nanum]   # runtime over the 18 cases
python lab/scripts/build_monitoring_suite.py && python lab/tests/browser_monitoring.py
python lab/scripts/build_gallery.py && python lab/tests/browser_smoke.py
python scripts/figure_metrics.py <specs...> [--root <checkout of the previous revision>]   # layout changes
```

`test_visual_spec.py` covers the spec layer: honesty fields, unknown keys/events/placeholders, unreadable
captions, bottleneck rules, flow model, author precision, compose layout, step targets, and the feedback
reproductions in `fixtures/feedback-*.json` (fictional content with the structure of an in-house figure).
`fixtures/postmortem-timeline.json` and `slow-degradation.json` are frozen specs from two reference cases;
`lab/tests/test_reference_specs.py` checks they still match the case builders.

Browser gates (`scripts/visual_gates.py`, run by `build_visual.py --check` and `lab/tests/browser_live.py`) need
Playwright and Chromium. They render our generated HTML with `set_content`, without external pages.

Verification layers are separate: unit tests; browser gates; human review of the screenshots and of a side-by-side
for visible changes; target Confluence (**not performed** by these tests). `test-cases.md` lists semantic
authoring scenarios; there is no automatic LLM evaluation.
