# Confluence Authoring Skill

## Purpose

Use this repository as a reusable authoring system when the user wants to create, edit, restructure, explain, summarize, or publish information in Confluence.

This is not a single document template. Choose the document structure and visual treatment from the user's purpose and source material.

## Start here

1. Understand the user's actual deliverable.
2. Identify the source of truth: current conversation, supplied files, code, issue tracker, existing Confluence page, or other explicitly available source.
3. If an existing Confluence page will be edited, read it before writing.
4. Read only the recipe and references needed for the task.
5. Use motion only when movement explains something that static content would explain poorly.
6. If the user explicitly asks to record/update/publish in Confluence and a write tool is available, perform the write and then read back the result.
7. Report what was changed, what evidence was used, and what was not verified.

## Source-of-truth rules

- Never turn an intention into a completed result.
- Distinguish planned / in progress / completed / blocked / unknown.
- Do not invent dates, metrics, owners, causes, or outcomes.
- When a value is illustrative, label it as illustrative.
- Preserve uncertainty when the source is uncertain.
- Prefer primary project material over recollection when both are available.

## Existing-page editing

When editing an existing page:

1. Read the current page.
2. Identify the smallest section that should change.
3. Preserve unrelated text, links, attachments, images, macros, anchors, and page structure.
4. Reuse the page's terminology unless the user explicitly requests terminology changes.
5. Avoid creating a replacement page merely because rewriting is easier.
6. Read the saved page after the change and compare the intended section.

## Recipe selection

Use the closest recipe under `recipes/` as guidance, not as a rigid form.

- weekly-report.md — periodic work notes, weekly agenda, short reporting
- project-status.md — status, milestones, risks, next actions
- technical-design.md — decisions, contracts, behavior, constraints
- architecture-explanation.md — components and interactions
- incident-analysis.md — symptoms, timeline, evidence, cause, recovery
- implementation-handoff.md — executable implementation instructions
- comparison.md — current vs proposed, option A vs B
- tutorial.md — concept teaching and step-by-step learning

If no recipe fits, compose a purpose-specific structure using `references/authoring-principles.md`.

## Representation selection

Choose the simplest representation that preserves meaning.

- prose: reasoning, context, nuanced explanation
- bullets: short independent facts
- table: repeated dimensions across comparable items
- callout: warning, decision, assumption, important constraint
- static diagram: structure or relationship that does not depend on time
- motion: progression, accumulation, transfer, transition, bottleneck, cause propagation

Do not add motion merely to make a page look more dynamic.

## Motion workflow

When motion is useful:

1. Read `references/motion-catalog.yaml`.
2. Select an implemented pattern whose `best_for` matches the explanation.
3. Read that pattern only.
4. Replace example labels and values with sourced content.
5. Use a unique alphanumeric prefix for every motion block on the page.
6. Keep a readable static final state.
7. Label synthetic or illustrative values.
8. Validate the rendered fragment with `scripts/validate_html_macro.py`.
9. If possible, verify the published Confluence page separately.

If only a planned pattern matches, use a static representation or explicitly create and register a new pattern. Never pretend a planned pattern already exists.

## Confluence HTML macro baseline

Read `references/confluence-rules.md` before generating HTML.

Default implementation profile:
- fragment only; no html/head/body wrapper
- CSS + SVG + semantic HTML
- no external network dependency
- no iframe
- no JavaScript unless the target environment is explicitly verified to allow it and it is materially necessary
- selectors, IDs, and keyframes scoped by a unique prefix
- responsive layout
- prefers-reduced-motion fallback
- print/static fallback
- explanatory text remains understandable without motion

## Visual style

Read `references/visual-guidelines.md`.

Default tone is technical, restrained, and readable. Motion directs attention; it does not decorate.

## Validation checklist

Before considering authoring complete:

- Content: important claims are supported by supplied or retrieved evidence.
- State: planned/in-progress/completed are not conflated.
- Structure: headings and hierarchy match the purpose.
- Preservation: unrelated existing page content was not damaged.
- Motion: selected only when useful; example data is labeled.
- HTML: no global CSS, unresolved template token, external dependency, duplicate prefix, or wrapper.
- Accessibility: static final state and reduced-motion behavior exist.
- Publishing: if a write was requested, saved content was read back.
- Verification: browser preview and actual Confluence verification are reported separately.

## Output report

For substantial edits, end with a compact report containing target page/draft, recipe used, visual patterns used, important source material, sections changed, validation performed, and remaining unverified items.

Do not expose secrets in the report.
