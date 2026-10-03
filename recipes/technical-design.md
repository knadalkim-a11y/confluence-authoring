# Recipe: Technical Design

Use for behavior, contracts, architecture decisions, runtime rules, or implementation constraints.

## Suggested structure
1. Problem and design goal
2. Scope / non-goals
3. Terminology
4. Proposed behavior
5. Components and responsibilities
6. Data / interface / state contracts
7. Permissions and failure behavior
8. Validation strategy
9. Migration or rollout considerations
10. Open questions

## Visual guidance (spec kinds: `references/visual-specs.md`)
`diagram` with `data_kind: "proposed"` for the target design; a second `diagram` with
`"current"` when the change is the point. Add `steps` when the order of interactions is the
core concept. Expected gains go in `bars` (before/after) with `data_kind: "estimate"`.

## Rule
Clearly label target design versus already implemented behavior.
