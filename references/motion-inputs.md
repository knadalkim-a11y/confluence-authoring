# Motion input contract — v0.2.0

`examples/motion-inputs.json` contains 13 illustrative inputs. Copy only the selected
object into a new UTF-8 JSON file. Do not silently use an example for measured data.

## Common inputs

Required: `title`, `description`, `caption`, `provenance`, `data_mode`.
`data_mode` is `illustrative`, `measured`, or `proposed`. Provenance must be nonempty.
Ordinary text is escaped; raw HTML and template tokens are not content inputs.
Optional: `duration` is 8..30 seconds (default 14); `repeat` is `1` (default) or
`"infinite"`. Duration is explanatory pacing, never a claimed real elapsed time.
A prefix is generated automatically unless explicitly supplied. Generate a fresh
prefix for each block added to the same page. Do not paste the same output twice.

## Pattern-specific inputs

| Pattern | Inputs and limits |
|---|---|
| line-reveal | `series`: 3..40 nonnegative finite numbers; `unit`, `x_label`; `change_index`: zero-based integer in series |
| threshold-cross | Same series/unit/x_label; `threshold`: nonnegative number; first strict `>` crossing is derived |
| recovery | Same series/unit/x_label; `incident_index` and later `recovery_index`: zero-based integers; these are supplied annotations, not detected causes/recovery |
| distribution-percentile | `values`: 2..14 unique ascending nonnegative values; equal-length `counts`: nonnegative integer frequencies, total > 0; `unit` |
| sequential-flow | `steps`: 1..6 nodes in sequence |
| before-after | `before`, `after`: each 1..6 nodes; same layout, no claimed speedup |
| parallel-flow | `start`, `join`: nodes; `left`, `right`: each 1..6 nodes; exactly two parallel routes |
| branch-flow | `decision`: text; `routes`: 2..4 text labels; `selected`: zero-based route index; no condition evaluation |
| approval-gate | `steps`: 1..6 nodes; `reviewer`, `gate`: text; final review is always waiting |
| retry-loop | `attempts`: 2..5 nodes; every node except the last must be `error`; bounded scenario, not an actual retry runner |
| request-response | `client`, `server`, `request`, `response`: text labels; decorative dots are not packet counts |
| queue-buildup | `arrivals`, `capacity`: equal-length lists of 3..10 nonnegative integers; optional `initial` backlog, default 0 |
| failure-propagation | `components`: 1..6 nodes in supplied cause-to-impact order; causal links require external evidence |

A node is a string (unknown status) or an object with `title`, optional `detail`,
and optional `state`: `done`, `waiting`, `error`, or `neutral` (default).
The badge says **final scenario state**, not live execution status. Unknown states
are not silently converted into successful completion. Text inputs have length
limits; unknown fields, nonfinite numbers, invalid indexes and malformed arrays fail.

## Numerical definitions

The line chart assumes equally spaced observations. Its geometry, table and summary
are computed together. Annotation timing uses cumulative drawn-path length.
For irregular time intervals, use a different renderer; do not label this as an
accurate real-time axis without transforming the input appropriately.

Distribution uses exact discrete observation values and frequencies, not arbitrary
histogram bin centres. Mean = sum(value × frequency) / total. P95 uses nearest-rank:
first value whose cumulative frequency reaches ceil(0.95 × total). Never insert a
user-provided average/P95 label while leaving the geometry unchanged.

Queue is a deterministic per-interval accounting example:
`served = min(previous_backlog + arrivals, capacity)`;
`backlog = previous_backlog + arrivals - served`.
It does not estimate probability distributions or elapsed waiting time.

## Generate

```sh
python scripts/render_motion.py parallel-flow rendered/flow.macro.html \
  --input my-flow.json --preview rendered/flow.preview.html
python scripts/validate_html_macro.py rendered/flow.macro.html
```

To inspect a reference instead of using real content:

```sh
python scripts/render_motion.py approval-gate rendered/example.macro.html --example
```

Legacy `render_template.py ... --set ...` still supports ordinary text templates.
It deliberately rejects v0.2 scene sources and explains the new command. Requiring
structured inputs prevents old hardcoded chart geometry from being relabeled as
unrelated data. Old v0.1 generated macros remain self-contained; they are not altered.
