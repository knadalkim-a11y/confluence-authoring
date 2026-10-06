# Contributing

This repository is a curated authoring library. Prefer a smaller set of reliable patterns over many near-duplicates.

## Add a recipe

Add a recipe when a recurring document purpose needs meaningfully different structure or verification rules.

A recipe should state:
- when to use it;
- the reader's goal;
- suggested structure;
- useful visual forms;
- failure/accuracy rules.

Do not create a new recipe for cosmetic formatting differences.

## Extend a visual kind

1. Start from the reader's question and a spec that the current kinds cannot express.
2. Prefer extending the compose engine (a container, part or routing rule that works in every figure) over a new kind.
3. Change the kind in `scripts/kinds/<kind>.py` and, if needed, its scene in `visuals/live/scenes/`.
4. Add a test to `tests/test_visual_spec.py` and an example spec to `examples/visuals/` when it is a new idea.
5. Run the checks in `tests/README.md`; for a visible layout change also `scripts/figure_metrics.py` against the
   previous revision and a side-by-side for review.

The CSS motion patterns (v0.1-0.3) are kept in `lab/` as reference; new visuals use the spec path.

## Avoid duplicates

Do not add a new kind or example merely for:
- another color;
- another project name;
- a different sample sentence;
- one extra stage when the existing kind can be parameterized.

## Compatibility

Confluence installations differ. Browser preview proves only browser rendering. A pattern is not "Confluence verified" until it has been published and checked in the target instance.

## Security

Never commit credentials, personal tokens, cookies, session values, or internal secrets to this repository.
