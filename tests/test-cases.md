# Test Cases

## Authoring behavior

### A01 — No forced motion
Input: short status update with three completed items.
Expected: concise prose/list/table; no motion unless progression is materially important.

### A02 — State honesty
Input: discussion says a feature will be implemented next week.
Expected: Planned; never Completed or Deployed.

### A03 — Existing page preservation
Input: update one section of an existing Confluence page containing links, images, macros, and unrelated sections.
Expected: only the intended section changes; unrelated assets and structure remain.

### A04 — Recipe is guidance
Input: a design note that partly matches technical-design but needs a short decision section.
Expected: adapt the recipe; do not force every heading.

## Motion selection

### M01 — Trend/change
Input: a metric remains stable and then rises.
Expected: `line-reveal` may be selected; units and data provenance are visible.

### M02 — Ordered workflow
Input: user action → automated execution → automated validation → human approval.
Expected: `sequential-flow`; human approval is not animated as automatically completed.

### M03 — Distribution/tail
Input: two latency distributions with similar averages and different tails.
Expected: `distribution-percentile`; sample size, unit, and percentile definition are sourced or clearly illustrative.

### M04 — Planned pattern
Input: queue buildup explanation before `queue-buildup` is implemented.
Expected: static diagram or explicit new-pattern work; never claim an implemented queue-buildup template exists.

### M05 — Multiple blocks
Input: two motion blocks on one page.
Expected: distinct prefixes; no duplicate IDs/keyframes.

### M06 — Reduced motion
Input: prefers-reduced-motion enabled.
Expected: readable static final state; no essential information depends on motion.

### M07 — Print/export
Input: browser print preview.
Expected: final state is readable and animation controls are unnecessary/hidden.

## Publication verification

### P01 — Local preview only
Expected report wording: Browser preview verified; Confluence rendering not verified.

### P02 — Published page read-back
Expected: saved page is re-read and content preservation checked.

### P03 — Published macro rendering
Expected: style, SVG, motion, and static/reduced-motion behavior checked separately from content save success.
