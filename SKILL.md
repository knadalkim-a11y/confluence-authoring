---
name: confluence-authoring
description: Create, edit, explain and structure general-purpose Confluence documents from conversations, files and project evidence. Select a flexible document recipe and, only when helpful, reusable static or animated explanations. Preserve existing pages and distinguish verified facts from proposals.
compatibility: Reading via authorized repository and Confluence tools; optional local HTML generation requires Python 3.10+. Browser tests require Playwright and Chromium.
metadata:
  version: "0.3.2"
---

# Confluence Authoring

This is a general authoring system, not a weekly-report form or an animation-only skill.
The user's purpose determines the structure. Reuse recipes as guidance, not mandatory headings.

## Start

1. Identify audience, purpose, source material, and requested destination/action.
2. Retrieve relevant source evidence. A repository is not permanently loaded memory;
   read the selected revision before claiming to use it. Pin the revision for the task.
3. For an existing Confluence page, read its current content and version before editing.
4. Read `references/authoring-principles.md` and only the necessary recipe.
5. Choose prose, table, callout, static diagram, or motion according to meaning.
6. Generate content; verify facts, states and preservation before any requested write.
7. Only publish/update when the user requests it and the connector actually supports it.
   Read the saved page back. Distinguish content-save verification from browser rendering.

## Source and edit rules

- Never convert planned work into completed, tested, approved or deployed work.
- Do not invent measurements, dates, owners, causes, improvements or access rights.
- Preserve uncertainty and separate facts, interpretation, proposals and examples.
- Keep changes to the smallest appropriate section. Preserve unrelated text, links,
  attachments, macros, IDs, anchors, layout and user edits.
- Re-read before writing when concurrent edits are possible. Use the current version
  supported by the tool. On conflict, reconcile; do not blindly overwrite the page.
- Do not create a replacement page or change sharing to make editing easier.
- A content request does not authorize changing this library, repository permissions,
  Confluence configuration, or authentication. Never store PATs, cookies or real internal
  content in this public reference repository.

## Flexible recipes

Read the closest relevant file under `recipes/`:

| Purpose | Recipe |
|---|---|
| Periodic agenda or work notes | weekly-report.md |
| Milestones, risks, present state | project-status.md |
| Behavior, design, contracts | technical-design.md |
| Components and interactions | architecture-explanation.md |
| Symptoms, evidence, recovery | incident-analysis.md |
| Executable implementation direction | implementation-handoff.md |
| Alternatives or before/after | comparison.md |
| Learning a concept or procedure | tutorial.md |

Compose a purpose-specific structure when none fits. Do not force a weekly-report
layout onto a technical explanation, tutorial, comparison or discussion record.

## Visual selection

Use text for nuance; tables for repeated comparable dimensions; static diagrams for
stable structure. Motion is optional: select it only for progression, accumulation,
transfer, branching, propagation or staged interpretation that benefits from movement.
Keep ordinary updates static. Read `references/visual-guidelines.md` for visual tone.

When motion helps:

1. Read the compact `references/motion-index.md`, not all HTML files.
2. Consult the selected entry in `references/motion-catalog.yaml` for fit and limits.
   Entries marked `planned` are not implemented patterns.
3. Read `references/motion-inputs.md`, the selected scene in `visuals/motion/`, and
   the matching object in `examples/motion-inputs.json` only as an illustrative example.
4. Supply a structured input with provenance. Use `scripts/render_motion.py` to
   compute geometry and assemble the shared player. Never change only chart labels.
5. Generate a unique prefix per block. The same output must not be pasted twice on
   one page. The renderer generates a random prefix by default.
6. Run `scripts/validate_html_macro.py` on the rendered fragment and on the combined
   macros where possible. A standalone preview uses a different wrapper from a macro.
7. Verify a readable static final state, controls, narrow layout and reduced motion.
8. Distinguish local browser results from actual target Confluence rendering.

If execution is unavailable, use a sourced static representation or clearly state
which generation/validation steps were not run. Never paste an unassembled scene
with template slots into Confluence or claim that a visual was verified from text alone.

## Composite reference examples

For multi-chart, resource-flow, distribution-comparison or timeline explanations,
read `references/monitoring-index.md` before assuming the basic 13 patterns are enough.
The v0.3 reference pack covers 18 cases in the linked monitoring article plus one
explicitly separate bonus. These are authored, synthetic reference examples, not
19 additional unrestricted measured-data import tools.

Read only the selected object in `examples/monitoring-cases.json` and its documented
limits. Generate with `scripts/build_monitoring_suite.py --case <id> --input <file>
--output <directory>`. Cases with empty `params` need implementation work to accept
new numeric sources; do not relabel their illustrative geometry as measured data.
The existing player is reused; no `stories/` hierarchy is required.

Read `references/monitoring-quality-review.md` for case-by-case decisions and
`references/monitoring-tests.md` for reproducible tests. Original text and published
code were inspected, but original live browser A/B and Confluence rendering were
not verified. Do not claim equal visual quality or frame rate from source review.
Preview and macro must embed the identical generated fragment, not a separate chat demo.

## Diagram layout

Read `references/diagram-layout.md` before drawing structure or request-flow diagrams.
Place and align nodes before animating them. Prefer straight connectors, use orthogonal
lanes only when needed, and use explicit boundary ports. Semantic event-loop circles
are an exception, not a reason to curve external connectors. Generate visible rails
and particle motion from the same route geometry. Read `references/layout-quality-review.md`
for the three v0.3.2 revisions; other reference cases have not all received this layout pass.
Preserve the 1.25x default and the numerical model when adjusting layout or playback.

## Runtime and publishing

Read `references/confluence-rules.md`. The default rendered macro is self-contained
HTML + CSS + inline SVG; no JavaScript, iframe, remote font, CDN or external request.
Shared source files are bundled into each output; Confluence does not fetch them.
The gallery may use JavaScript for search/selection, but macro code does not.
The default animation plays once and retains the final state; replay is user controlled.

HTML macro availability is environment-specific. An enabled macro does not prove
that every SVG/CSS/input element survives sanitization. Do not change server security
settings. When publishing is unsupported, return the draft and fragment rather than
claiming a successful edit.

## Completion report

For substantial edits, report the target page/draft, source revision, recipe and patterns,
sections changed, generation/validation performed, and unverified aspects. Sources and
computed data must support visible conclusions. Do not expose credentials or claim
installed-skill activation just because SKILL.md exists in a GitHub repository.
