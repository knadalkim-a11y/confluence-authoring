# Recipe: Architecture Explanation

Use when teaching how a system is composed and how pieces interact.

## Suggested structure
1. One-paragraph orientation
2. Main components
3. Responsibilities
4. Interaction paths
5. State/data ownership
6. Boundaries and permissions
7. Common scenario walkthrough
8. Failure/edge cases

## Visual guidance (spec kinds: `references/visual-specs.md`)
- `diagram` without steps for structure, boundaries (`groups`) and ownership; set `data_kind`
  to `current` or `proposed` so readers know which one they are looking at
- `diagram` with `steps` when the point is the path a request or data takes (agent calls,
  pipelines, approvals); one diagram per claim
- never use motion to compensate for unclear component names
