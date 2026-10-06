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

## Add a motion pattern

1. Define the explanation problem first.
2. Add metadata to `references/motion-catalog.yaml`.
3. Implement the pattern under `visuals/motion/`.
4. Use `{{PREFIX}}` for every selector/ID/keyframe namespace.
5. Keep the fragment free of external dependencies.
6. Add reduced-motion and print/static behavior.
7. Make example/synthetic data explicit.
8. Add or update a gallery example.
9. Add a test case.
10. Validate a rendered instance.
11. Only then change catalog status from `planned` to `implemented`.

## Avoid duplicates

Do not add a new pattern merely for:
- another color;
- another project name;
- a different sample sentence;
- one extra stage when the existing pattern can be parameterized.

## Compatibility

Confluence installations differ. Browser preview proves only browser rendering. A pattern is not "Confluence verified" until it has been published and checked in the target instance.

## Security

Never commit credentials, personal tokens, cookies, session values, or internal secrets to this repository.
