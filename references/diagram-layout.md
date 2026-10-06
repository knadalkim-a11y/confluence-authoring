# Diagram layout contract — v0.3.2

Apply before animating a structure, request flow, pipeline or execution mechanism.
This contract is general; the current implementation covers the cascade, event-loop
and pipeline-bottleneck reference cases, not every diagram in the library.

## Layout first

Choose the flow direction and meaningful levels before placing nodes. Peers have the
same size, alignment and repeatable spacing. Treat input, processing, dependency and
auxiliary work as different roles. A narrow layout may rotate the primary flow but
must preserve identities, states and the same animation clock.

## Edges and ports

Use a single straight segment when unobstructed, including a diagonal fan. Use
orthogonal segments only to avoid collisions or to express a shared distribution
lane. External connectors contain no decorative Bezier curves. Keep semantic circles
inside an event loop; this is not permission to curve unrelated external wiring.

Use explicit boundary ports: left/right centres for horizontal primary flow,
top/bottom centres for vertical flow. An auxiliary return path may use another face,
but it must be named, repeatable and outside unrelated nodes. Arrow direction and
port position must agree. Lines must not cut through node bodies or labels.

Intentional buses are drawn once. Branch junctions are visible. Never superimpose
several complete routes to imitate a bus, and never confuse a shared junction with
an accidental crossing. The narrow cascade uses separately named input/output buses.

## One geometry for line and motion

`lab/scripts/diagram_layout.py` (reference cases) contains small explicit node/route definitions, not a new
story hierarchy or generic graph engine. A `Route` owns its point list. Both the
visible SVG rail and CSS motion path serialize that same list with `path_d()`.
For shared buses, a composite route names the visible rail parts it follows.
Circular task execution is an internal semantic path, with endpoints matched to the
actual dispatch, response or I/O ports. Do not maintain an independent curve for dots.

Keep numerical models separate from geometry. Changing alignment or speed must not
change arrivals, queue accounting, exclusions, completed tasks or failure assumptions.
The CSS macro has no JavaScript, network dependency or server-setting requirement.

## Required checks

- Peer alignment/size/gap; nodes inside canvas; no node overlaps.
- Exact port endpoints; only straight/orthogonal external edges.
- No unrelated node penetration or unintended proper edge crossings.
- A composite bus motion path lies on the union of its visible rail parts.
- Rendered token centres coincide with the path at intermediate times, not just ends.
- Visible SVG labels do not overlap at normal, transitional and final states.
- Wide and 390/320px layouts; resizing does not restart a second clock.
- Pause/resume/replay, final state, reduced motion, print and unique prefixes.
- Gallery preview, source view and exported macro represent the same selected version/speed.

These checks do not establish original-site equivalence, comprehension, real FPS or
actual Confluence compatibility. Record those separately and never infer them from lint.
