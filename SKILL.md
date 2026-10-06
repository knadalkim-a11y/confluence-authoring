---
name: confluence-authoring
description: Create, edit, explain and structure general-purpose Confluence documents from conversations, files and project evidence, and make report visuals that fit the situation (backlog/capacity flows, metric trends around events, comparisons and before/after, funnels, composition, schedules and incident timelines, architecture and process diagrams including AI agent and RAG request paths; animated only when movement explains). Builds validated Confluence HTML macros plus standalone HTML, SVG and PNG figures from a JSON spec. Preserve existing pages and distinguish verified facts from proposals.
compatibility: Reading via authorized repository and Confluence tools. Building visuals requires Python 3.10+ and Node.js (it renders the static scenes); the browser quality gates and PNG export need Playwright with Chromium (without them builds still succeed and report the gates as not run).
metadata:
  version: "0.19.1"
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

Use text for nuance and decisions; tables for exact values or many dimensions; a visual only
when the reader must see a shape, a comparison or a mechanism. Each visual makes one claim.
Read `references/visual-guidelines.md` for the visual language.

To make a visual for a report or document, use the spec path (default):

1. Read `references/visual-specs.md`. Pick the kind by the reader's question: `flow`
   (backlog, queue, capacity, bottleneck), `trend` (metrics over time, around an event,
   against a target), `bars` (comparison, before/after; `"mode": "funnel"` for drop-off
   between steps), `share` (how a whole splits and how the split changed; instead of a pie),
   `timeline` (schedule; incident minutes with `HH:MM` times), `distribution` (how values
   spread; mean vs percentiles), `diagram` (architecture,
   components and connections; with `steps` the path a request, document or approval takes,
   e.g. an AI agent call; `data_kind` `current` or `proposed`), `concept`
   (compare / stack / sequence presets) and `compose` for any other idea: nest layout containers (row, column,
   grid, stack, split, lifelines) and parts (elements with states, code, badges and bubbles;
   frames and boundaries; links) so the figure has the idea's own shape instead of the
   nearest template's.
2. Copy the closest spec from `examples/visuals/` and replace claim, data, source and
   `data_kind` (`measured` / `estimate` / `example`). Bind captions to model events; put
   computed numbers in text through placeholders, never by typing them.
3. Build and gate: `python scripts/build_visual.py spec.json --out <dir> --check`.
   Exit 0 = built and checked, 1 = a `FAIL` to fix, 2 = built but the browser gates could
   not run (no Playwright/Chromium): say so instead of reporting it as checked.
   Fix what a `FAIL` names; then look at the screenshots in `<dir>/shots/` at both widths
   and revise until the picture shows the claim at a glance and boxes with the same role line up.
   `report.json` lists the layout decisions (`layout`: folded, wrapped, aligned, rerouted, height per part)
   and clutter numbers; read them instead of guessing when a layout surprises you.
4. Paste `<dir>/macro.html` into one HTML macro per visual. Animated output needs inline
   scripts in the target Confluence (smoke check in `confluence-rules.md`); otherwise
   rebuild with `"motion": "none"` for a static figure of the same quality. For slides,
   word processors or wikis without HTML embedding use `<dir>/figure.svg` or `figure.png`.
5. Report the spec, mode, gate result and what was not verified.

Each recipe in `recipes/` names the kinds that usually fit it.

For a mechanism no kind expresses, write a custom live scene (`references/live-runtime.md`;
thread-pool is the worked example) and run the same gates.

Legacy: the 13 CSS motion patterns (`references/motion-index.md`, `scripts/render_motion.py`)
predate the spec path and its visual language. Use them only when an animated explanation
is required and the target Confluence cannot run inline scripts. Entries marked `planned`
in `references/motion-catalog.yaml` are not implemented. Validate any fragment with
`scripts/validate_html_macro.py`, verify the static final state, narrow layout and reduced
motion, and distinguish local browser results from target Confluence rendering.

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

Cases with `"runtime": "live"` (thread-pool, pipeline-bottleneck, bounded-queue, cpu-latency) are built by the live
runtime; three of them are plain specs of the generic kinds (see `visual-specs.md`), thread-pool is a
custom scene. Read `references/live-runtime.md` for layers and gates. Building needs Node.js.

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

Read `references/confluence-rules.md`. Static output (spec `motion: "none"`, and
static kinds) is self-contained HTML + CSS + inline SVG: no JavaScript, iframe, remote font, CDN
or external request. Animated spec output and live scenes carry one validated, bundled inline
script per block plus static final-scene SVGs (wide and phone), used only after the target
Confluence is checked to run inline scripts (smoke check in confluence-rules.md).
Shared source files are bundled into each output; Confluence does not fetch them.
The gallery may use JavaScript for search/selection; static macros do not.
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
