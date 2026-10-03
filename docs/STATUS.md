# Status — v0.3.2 layout revision

Review branch: `feat/initial-authoring-skill`, existing Draft PR #1.
Remote starting point: `a4334ef6f0d9b063dd6b246765199bf4ada4a28f`.
Local starting point: delivered v0.3.1 ZIP (previously not pushed).
No main merge, Draft removal, release, permission change or Confluence publication.

## Changed

- Preserved v0.3.1 mechanism models and the 1.25x default / three-speed gallery.
- Cascade: equal peer nodes/gaps; centred LB/DB; straight desktop fan; two deliberate,
  single-stroke mobile trunks with visible branch junctions.
- Event loop: aligned primary flow; direct I/O delegation and orthogonal callback
  return. External curves removed. Internal circular execution remains meaningful.
- Pipeline: equal node sizes/gaps, explicit queue block, straight shared-axis ports;
  equivalent top-down narrow layout. Existing fluid-accounting model preserved.
- Visible rails and moving tokens use one Route point list; SVG port markers expose
  endpoints. No stories hierarchy or dependency on an external layout library.
- Before/after gallery toggle compares the previous v0.3.1 and current versions of
  these three cases at the same selected speed.

## Actual validation

54 available Python test methods pass (30 prior monitoring + 12 prior mechanism +
12 new layout tests). All 19 reference macros pass static lint and local Chromium
regression. Additional geometry checks cover the three revised cases at 1160/390/320px,
intermediate token positions, label overlap, clock preservation on resize, and exact
old/current preview/code/export at 1x, 1.25x and 1.5x. See tests/layout-verification.json.

The other 16 generated macros are byte-identical to the delivered v0.3.1 at the same
prefix/speed. The three original numerical models are identical after excluding the
new layout metadata. Their input assumptions have not been changed by this revision.

## Boundaries

Original-site live A/B, target Confluence rendering, other browser engines and real
frame-rate measurements: not verified. This is a rendering-source snapshot test,
not a fresh git clone or GitHub Actions run. The 13 basic pattern suite and 8 document
recipes remain outside this change and were not re-tested here. Historical reports
retain their original scope; tests passing is not a visual-equivalence rating.
