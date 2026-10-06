# Document visuals from a spec (v0.10.0)

Purpose: when someone wants a visual for a report or document, write a short JSON spec that
states the claim, the data and its provenance; `scripts/build_visual.py` computes the model,
lays it out in the house visual language, binds captions to model events, and checks the
result. The author decides *what to say*; the library decides *how it looks* and refuses
specs it cannot render well.

## 1. Draw only when a picture says it faster

- **Prose** for causes, caveats and decisions. **Table** for exact values a reader looks up,
  more than ~12 items, or many dimensions.
- **Visual** when the reader must see a shape, a comparison or a mechanism. Write the claim
  first (one sentence). If you cannot, do not draw.
- One visual, one claim. Two different claims → two visuals separated by text.

## 2. Choose the kind by the reader's question

| The reader needs to see… | Kind | Default motion |
|---|---|---|
| how work piles up in front of a limit (backlog, queue, capacity, bottleneck, throughput), or what changes with more capacity or a queue limit | `flow` (one lane, or two variants side by side) | animated: accumulation is the point |
| how metrics moved over time, around an event (release, change, incident), against a target | `trend` | animated when captions tell a story (≥ 2 captions), else static |
| how a few categories compare, or before vs after per item (same unit) | `bars` | static |
| where people drop out of a sequence of steps (sign-up, hiring, conversion) | `bars` with `"mode": "funnel"` | static |
| how a whole splits into parts, and how that split changed (cost mix, cause mix) | `share` | static |
| a schedule: phases, status, milestones, today; or an incident's minutes (detection, response, recovery) | `timeline` (dates, numbers, or `HH:MM` clock times; `"durations": true`) | static |
| what the parts of a system are and how they connect (architecture, data pipeline, ownership, current vs proposed) | `diagram` | static |
| the path a request, document or approval takes through those parts (AI agent call, RAG, approval process, failure propagation) | `diagram` with `steps` | animated, one step at a time; the step list stays in the picture |
| how values spread, and what the average hides (latency, durations, any per-item measure) | `distribution` | dots arrive, then mean / P50 / P95 / P99 one at a time |
| an idea side by side: without vs with, before vs after, two viewpoints | `concept` `"form": "compare"` | columns enter in turn |
| what something is made of, top to bottom (a context window, layers, an organisation) | `concept` `"form": "stack"` | bands settle bottom-up |
| who sends what to whom, in order (an API call, a tool call, a hand-off) | `concept` `"form": "sequence"` | messages drawn one by one |
| an idea whose shape none of the rows above fit: things inside a boundary, chosen vs not chosen, a parent and its children, a loop back, content that changes as it crosses a boundary, assumptions each side makes | `compose` (a tree of layout containers and parts, §4) | each top-level part enters in turn, or your `steps` |
| a mechanism none of these express (discrete workers, retries, routing, cycles) | custom live scene, see `live-runtime.md` (thread-pool, cfs, cascade, eventloop, timeout are examples) | animated |

Deliberately not offered: pie/donut, 3D, dual y-axes, KPI gauge tiles, decorative motion.
`motion: "none"` forces a static figure (use it when the target Confluence does not run inline
scripts); `"play"` animates a kind that is static by default (bars grow once).

## 3. Fields every spec has

| Field | Rule |
|---|---|
| `kind` | `flow` · `trend` · `bars` · `share` · `timeline` · `diagram` · `distribution` · `concept` · `compose` |
| `title` | Accessible name (≤ 120 chars). The page heading usually says it too. |
| `claim` | The one-sentence takeaway (≤ 120). Shown under a static figure; use it as the last caption of an animated one. |
| `source` | Where the numbers come from. Required. |
| `data_kind` | `measured` · `estimate` · `example`; for `diagram`, `concept` and `compose`: `current` (현재 구조) · `proposed` (제안안) · `example`. Required; shown in the picture or notes so illustrative numbers or a proposal are never mistaken for the real thing. |
| `motion` | `auto` (default) · `play` · `none` |
| `captions` | `[{"at": time or event, "text": "…"}]`. One claim each, 25–45 chars (hard limit 50 after placeholders). Bind to model events, not guessed times. The build fails if two captions are too close to be read at the default speed. |

Numbers inside text come from the model through `{placeholders}`; unknown placeholders and
unknown events are build errors that list what is available. Never type a computed number.

## 4. Kinds

### `flow` — inflow, stages with limits, queue in front of the narrowest stage

```json
{"kind": "flow", "title": "…", "claim": "…", "source": "…", "data_kind": "example",
 "time": {"unit": "일", "end": 20}, "units": {"rate": "건/일", "count": "건"},
 "inflow": [[0, 90], [5, 120], [15, 90]],
 "stages": [{"name": "상담팀", "capacity": 100}],
 "variants": [{"name": "현재 4명", "tone": "bad", "capacity": 100}, {"name": "5명", "tone": "good", "capacity": 125}],
 "queue": {"limit": null},
 "labels": {"inflow": "유입", "wait": "새 문의 대기", "spare": "여유", "limit_pill": "한도 도달"},
 "captions": [{"at": 0, "text": "…"}, {"at": "change", "text": "…"}, {"at": "wait:1", "text": "…"}],
 "callouts": [{"lane": 0, "at": "wait:1", "text": "하루 넘게 대기", "tone": "hot"}]}
```

- Model: deterministic fluid queue (inflow − service, integrated) in front of the narrowest
  stage; FIFO; wait = queue ÷ bottleneck capacity. Stages before the bottleneck must handle the
  peak inflow (else the queue would form there; the build says so). 1–4 stages, ≤ 2 variants
  (variants may change the bottleneck `capacity` or the queue `limit`), ≤ 8 inflow steps,
  queue limit ≤ 40. Names longer than 8 chars need `short` for phones.
- Picture: stages with limit, thick gauge and %; a compact queue right in front of the
  bottleneck (red dots while it is the problem, the count above it; the dot scale is in the
  notes) or limit cells (one cell = one request); rejected requests leave in red; the
  bottleneck is the red box, other stages get "여유" pills while a queue exists. Two
  single-stage variants sit side by side with per-lane readouts and a wait-time sparkline;
  a single lane gets a "대기 추이" strip only when the backlog drained before the end, so the
  printed/no-JS picture still shows it.
- Events: `start`, `end`, `change`, `change:2`…, `queue`, `drain`, `peak`, `full`,
  `wait:0.5|1|2|3|5|10` (wait reaches that many time units); add `@1` for the second variant.
- Placeholders: `inflow_start`, `inflow_peak`, `inflow_end`, `change`, `end`, `time_unit`,
  `rate_unit`, `count_unit`; per lane (`@1` for the second): `queue_end`, `served_end`,
  `rejected_end`, `wait_end`, `capacity`, `bottleneck`, `reject_rate`, `limit`, `limit_wait`,
  `limit_wait_ms`, `excess`; event times as `t_<event>` (e.g. `{t_drain}`, `{t_wait:1}`), in time units.

### `trend` — metrics on one shared time axis

```json
{"kind": "trend", "time": {"unit": "주", "end": 12, "ticks": [[0, "1주"], [6, "7주"], [12, "13주"]]},
 "panels": [{"label": "배포 리드 타임 (일)", "unit": "일", "max": 8, "ticks": [8, 4, 0], "decimals": 1,
             "series": [{"name": "리드 타임", "color": "blue", "points": [[0, 6.5], [1, 6.8]]}]}],
 "events": [{"at": 6, "label": "CI 병렬화"}],
 "thresholds": [{"panel": "배포 리드 타임 (일)", "value": 3, "label": "목표 3일"}]}
```

- 1–4 panels stacked on one time axis (use `groups` for up to 3 side-by-side columns, each
  with `pill`/`note` timelines `[[at, text, tone]]`, as in the CPU example). ≤ 3 series per
  panel (legend appears automatically); points must cover `0..end`. Colours: blue, purple,
  green, red, amber, gray. Value labels sit at the cursor and avoid each other and events.
- Article vocabulary (v0.9.2), each shown only from its time on:
  `events[].color` colours an event line and its label (labels stack so they never touch);
  `bands: [{"from", "to", "label": "감지 공백 {duration}", "color"}]` shades an interval in every
  panel and brackets it above, `{duration}` computed; `annotations: [{"at", "panel", "series",
  "text", "color", "side"}]` writes bold text at that series value (placeholders allowed, e.g.
  `{P99_change_pct}% ({P99_start}ms → {P99_end}ms)`); `between: [{"panel", "upper", "lower",
  "from", "to", "color"}]` shades the gap between two series (week-over-week); group `title`
  + `color` heads a column (정상 / 누수). A series may cover only part of the axis (a copied
  week laid over the last one). A threshold near the top edge puts its label under the line.
- More (v0.10.0): up to 4 groups (2 x 2 grid), `groups[].events` for one column only (scenario A
  / B), series `style: "dashed"`, `dots: true`, `area: false`, `label: false` (helper line: no
  value label, no legend entry), panel `hide_label`, pill tones `bad` and `purple`,
  `stream: {"after": panel, "label", "box", "side", "phases": [{"from", "divert", "color",
  "divert_color", "note"}], "end_note"}` (a row of requests between panels; `divert` = share
  failing fast or going to the side box, from the model) and `log: {"label", "lines": [[at,
  text], [at, text, "hot"]]}` (log lines aligned with the chart clock; the hot line is the culprit).
  Value labels are dropped where no free spot exists; the reading is in the table.
- Events: `start`, `end` and every event `label` (or `name`).
- Placeholders: `<series name>_end`, `_max`, `_start`, `_change_pct` (non-word characters → `_`, e.g.
  `{리드_타임_end}`), `@i` suffix for group i > 0; `end`, `time_unit`.

### `bars` — categories, or before/after pairs

```json
{"kind": "bars", "unit": "억 원", "items": [{"label": "1분기", "value": 11.2}],
 "highlight": ["4분기"], "target": {"value": 15, "label": "목표 15억"}}
{"kind": "bars", "unit": "분", "better": "lower", "flat_pct": 10, "pair_labels": ["개선 전", "개선 후"],
 "items": [{"label": "빌드", "before": 18, "after": 6}]}
```

- ≤ 12 items, one unit and one scale for all. Decimals follow the author's data (12.8 stays
  12.8). Pairs show the change in %; `better` sets which direction is good; changes within
  `flat_pct` read "≈ 그대로" instead of a misleading coloured percentage.
- `"mode": "funnel"`: items in step order, each ≤ the previous. Each row shows its conversion
  from the previous step and the people lost ("25.8% (−8,900명)"); the overall conversion is
  printed under the bars. `"drop": "rate"` (default) marks the lowest conversion, `"count"` the
  step that loses most people. "가장 많이 이탈" is ambiguous: these can be different steps, so
  say which one the claim means and set `drop` to match.

### `distribution` — one dot per observation, and what the average hides

```json
{"kind": "distribution", "unit": "ms", "max": 1000,
 "groups": [{"label": "서버 A", "values": [70, 100, 130], "counts": [4, 30, 6]},
            {"label": "서버 B", "values": [22, 42, 470, 850], "counts": [26, 8, 5, 1]}],
 "markers": ["mean", "p50", "p95", "p99"], "tail": {"from": 400, "label": "긴 꼬리 (요청의 {share}%)"},
 "captions": [{"at": 0, "text": "…"}, {"at": "mean", "text": "평균은 둘 다 {mean}ms"}, {"at": "tail", "text": "…"}]}
```

- 1–3 samples side by side (stacked on phones), ≤ 120 observations each, values increasing.
  Mean and percentiles are computed in Python; each marker appears at its own event (`mean`,
  `p50`, `p95`, `p99`, `tail`); placeholders `{mean}`, `{p99}`, … (`@1` for the second sample).
- `tail` shades the values at or above `from` where a sample has any, with `{share}` computed.

### `share` — composition (100% bars)

```json
{"kind": "share", "categories": ["컴퓨팅", "DB", "스토리지", "네트워크", "기타"],
 "rows": [{"label": "작년", "values": [61, 12, 14, 10, 3]}, {"label": "올해", "values": [52, 14, 18, 12, 4]}],
 "unit": "%", "highlight": "컴퓨팅"}
```

- 2–6 categories, 1–4 rows. With `"unit": "%"` each row must add to 100 (±1); with any other
  unit (e.g. `"억 원"`) rows are normalised and raw values go to the table. `highlight` makes
  that category the only saturated one and prints its change in %p between the first and last
  row. Percentages appear inside a segment only where they fit; the table has all of them.
  Category names are written inside segments where they fit. Use `share` instead of a pie chart.

### `timeline` — schedule

```json
{"kind": "timeline", "time": {"start": "2026-01-05", "end": "2026-04-03"},
 "tracks": [{"label": "개발", "start": "2026-02-09", "end": "2026-03-20", "status": "late", "note": "+1주"}],
 "milestones": [{"at": "2026-03-23", "label": "베타 오픈"}], "today": "2026-03-02"}
```

- ≤ 10 tracks; status `done` · `active` · `planned` · `late` · `risk` (legend lists only those
  used). Dates as `YYYY-MM-DD` (month ticks), numbers with `time.unit` (e.g. weeks), or clock
  times `HH:MM` (ticks every 5–240 min; times after midnight wrap). `"durations": true` writes each
  track's length (e.g. "3분", "1시간 20분", "12일") where no `note` is given. `today_label`
  renames the today line (e.g. "현재"). The status legend speaks schedule language (완료, 진행,
  예정, 지연, 위험): for an incident or anything else set `"legend": false` (the track labels
  already name the phases) or rename with `"status_labels": {"late": "감지 공백"}`.
- Static kinds print "예시 데이터" / "추정값" in the picture when `data_kind` is not `measured`.

### `concept` — ideas, not numbers (v0.15.0; presets of `compose` since v0.16.0)

The spec below is unchanged; the drawing is the `compose` engine (compare = `split`, stack = `stack`,
sequence = `lifelines`). Three forms that recur in hand-made explanation figures (docs/design/motion-concept-architecture.md §10). All use
the role tones; all animate by default (each unit enters in turn) and settle into the final scene.

```json
{"kind": "concept", "form": "compare", "data_kind": "example", "arrow": "검색 추가",
 "columns": [{"label": "모델만 사용", "tone": "red", "items": [{"name": "그럴듯한 추측", "sub": "출처 없음"}], "note": "…"},
             {"label": "검색 + 모델", "tone": "blue", "items": [{"name": "근거를 붙인 답변", "tone": "green"}]}]}
{"kind": "concept", "form": "stack", "bracket": "컨텍스트 창", "free": "남은 공간",
 "layers": [{"name": "시스템 프롬프트", "sub": "역할·규칙", "tone": "blue"}, {"name": "이전 대화", "tone": "amber", "size": 3}]}
{"kind": "concept", "form": "sequence", "actors": [{"id": "user", "name": "직원"}, {"id": "agent", "name": "에이전트", "tone": "purple"}],
 "messages": [{"from": "user", "to": "agent", "text": "남은 연차 알려줘"}, {"from": "agent", "to": "user", "text": "11일", "style": "dashed"}]}
```

- compare: 2-3 columns, 1-6 items each (name ≤ 16, sub ≤ 22), optional `note` (≤ 40) and `arrow` label (≤ 10)
  between columns. Columns sit side by side on wide screens and stack on phones (or when the arrow label would
  need too wide a gap). Keep ≤ 4 items per column with 3 columns, or phones exceed the height budget.
- stack: 2-7 bands listed top to bottom (name ≤ 18, sub ≤ 28, `size` 1-3 relative height), optional `bracket`
  (side label ≤ 12) and `free` (an empty dashed band on top, ≤ 14). Name and sub share a line when there is room.
- sequence: 2-4 actors (name ≤ 10), 1-8 messages in order (text ≤ 24; `style: "dashed"` = reply), numbered.
- Not for numbers (use a chart kind), not for a system's structure (use `diagram`), not for metaphors (seesaw,
  explosion): those stay prose or a custom scene.

### `compose` — build the figure from parts (v0.16.0)

When the idea does not fit a preset, compose it. A figure is one tree: layout containers hold parts and other
containers; every part works in every container. Pick containers by how the reader should scan the idea, then
add only the parts that carry the claim.

```json
{"kind": "compose", "data_kind": "example", "title": "…", "claim": "…", "source": "…",
 "root": {"layout": "row", "items": [
   {"layout": "column", "id": "cands", "label": "스킬 후보", "items": [
     {"id": "rv", "name": "코드 리뷰", "state": "muted"}, {"id": "ts", "name": "테스트 작성", "state": "muted"}]},
   {"layout": "stack", "frame": "solid", "label": "컨텍스트 윈도우", "free": "남은 공간", "items": [
     {"id": "ins", "name": "코드 리뷰 스킬", "state": "selected"}, {"name": "대화 기록", "tone": "amber", "size": 2}]}]},
 "links": [{"from": "rv", "to": "ins", "label": "주입"}],
 "steps": [{"show": ["cands"], "caption": "쓸 수 있는 스킬은 여럿이다"},
           {"set": {"rv": "selected"}, "caption": "필요한 스킬만 고른다"},
           {"show": ["ins", "L0"], "caption": "고른 스킬만 창에 들어간다"}]}
```

Containers (`layout`, nest up to 4 deep):

| layout | holds | use it for |
|---|---|---|
| `row` | 1-5 parts side by side; `sep` (≤ 8, e.g. "경계") draws a dashed boundary between neighbours | a chain, a before→after pair of things, two sides of a boundary |
| `column` | 1-7 parts top to bottom; `bracket` (≤ 12) side label | a list, a vertical flow, a parent above its children |
| `grid` | 2-12 parts, `cols` 2-4 | many peers (modules, teams) |
| `stack` | 2-7 elements as touching bands (`size` 1-3), `bracket`, `free` (empty band on top) | what something is made of |
| `split` | 2-3 containers with dashed dividers, `arrow` (≤ 10) between them | without vs with, before vs after, two viewpoints |
| `lifelines` | 2-4 actors + `messages` (as `concept` sequence) | who sends what to whom |

Any container: `id`, `label` (≤ 18), `tone`, `frame` (`"solid"` a group, `"dashed"` a boundary), `note` (≤ 40,
under it), `banner` (≤ 40, a tinted bar under it: the consequence), `span` (≤ 24, an arrow over its width: one
operation across all of it), `grow` (1-3: in a row, containers share the width the elements leave in this ratio).

Elements: `id` (needed to link or step), `name` (≤ 16; 18 in a stack), `sub` (≤ 22), `shape` (`box` · `pill` ·
`cylinder` storage · `doc` file/document), `tone` (inherits the container's), `state` (`normal` · `selected` ·
`muted` not chosen / idle · `error` · `ok`), `code` (≤ 5 lines × 30 chars: the data itself, e.g. a row, JSON),
`badge` (`{"text": ≤ 10, "kind": ok|bad|warn|info}`), `bubble` (≤ 26: what this side assumes), `size`, `grow` (1-3: in a
row, the element is this many times its natural width; it is not a share of the row),
`dashed` (true: outside your control, e.g. an external service), `bar` (0-1: a relative amount drawn as a bar inside
the box; say what it means in `sub` or a note; it is not a measured number).

Links: `{from, to}` element ids, `label` (≤ 14), `style` (`flow` request/data, default, a dot travels it once ·
`reply` dashed answer · `hidden` a dependency the code does not show · `fail` broken, with ✕ · `none` explicitly
no connection), `via` (`left`/`right`: loop around the side, e.g. retry), `id` (default `L0`, `L1`, … in order),
`token` (false: no travelling dot).

Steps (optional, 1-6): `show` (ids of elements, containers = all inside, links, lifeline messages `<id>.m<k>`),
`set` (`{id: state}` or `{id: {"state": …, "badge": {…}}}`: a state change, animated; the chip swaps with it),
`path` / `paths` (element ids along existing links, 1-3 routes: the route stands out for the step and one dot
travels it), `caption` (≤ 60; the step lasts until it can be read). Without `steps` each top-level part enters in
turn (a stack bottom-up). Parts never shown by a step are there from the start (context).
Every captioned step is numbered, and its number is drawn on the part the step is about (the first thing it
shows, changes or follows): a box's corner, after a group's name, or in a link's or message's label. The list or
caption line and the picture therefore pair one to one; the build fails when a number has no part in the final
picture or is cut off. Steps must name parts by the `id` you gave them (not the engine's `k1`, `e3`), and never
the whole figure. Group names and split headers sit on the content they label, not on the container's share.

Figure level: `step_list: true` keeps the numbered step captions in the picture (current one highlighted; print and
the no-JS figure keep the story; the caption line then shows the claim), `legend` (≤ 5 entries
`{"tone" | "style" | "shape", "dashed"?, "text": ≤ 20}`, drawn at the bottom left).

What the engine does for you, so the spec never carries coordinates:
- Rows give elements their natural width and containers the rest; gaps grow to fit link labels. A row that does
  not fit first narrows its gaps (labels wrap at spaces), then wraps into evenly filled lines (a chain continues
  in snake order), and only then folds into a column. Splits stack on phones; framed containers in a row share a height.
- Links are orthogonal: straight when the boxes face each other, one elbow in the gap between the two branches
  otherwise (a parent and its children get a trunk and a bus), around the side when the direct path would cross
  a box (on phones a side gutter is made for it). Labels go to the first place that clears every box and label.
- Gates for every part: text stays in its box, no line through another box, boxes and frames nest (never half
  overlap), no one-frame colour switch on a state change, token pace, plus all the shared gates.

Not for numbers (use a chart kind), and not for metaphors (tangled lines, a seesaw): say those in prose. Keep
one claim per figure; if it needs more than ~12 elements, split it.

### `diagram` — components, connections, and the path through them

```json
{"kind": "diagram", "data_kind": "proposed",
 "layers": [{"label": "사용자", "nodes": [{"id": "user", "name": "직원", "sub": "Slack", "type": "person"}]},
            {"label": "에이전트", "nodes": [{"id": "agent", "name": "사내 에이전트", "type": "ai"}]},
            {"label": "도구", "nodes": [{"id": "rag", "name": "문서 검색", "type": "data"}, {"id": "llm", "name": "LLM", "type": "external"}]}],
 "groups": [{"label": "사내망", "layers": [0, 1]}],
 "edges": [{"from": "user", "to": "agent", "label": "질문"}, {"from": "agent", "to": "rag", "label": "검색"},
           {"from": "rag", "to": "agent", "label": "문서"}, {"from": "agent", "to": "llm", "style": "dashed"}],
 "steps": [{"path": ["user", "agent", "rag", "agent"], "text": "에이전트가 사내 문서를 먼저 찾는다"},
           {"paths": [["agent", "llm"], ["agent", "rag"]], "text": "두 요청이 동시에 나간다"}]}
```

- Layers run left to right on wide screens and top to bottom on phones (same picture, rotated).
  1–5 layers, 1–4 components per layer, ≤ 14 components, ≤ 24 connections. Order components
  inside a layer to keep lines short. `name` ≤ 14 chars (wraps to two lines), `sub` ≤ 18
  (dropped on phones when it does not fit; the table keeps it). `type`: `system` (default),
  `person` (rounded), `ai` (purple: models, agents), `data` (green: stores, indexes),
  `external` (dashed: outside services); the legend lists the types used.
- Connections join adjacent layers or neighbours in one layer. A connection that skips layers
  runs in a lane outside every box, so both ends must be first (lane above / left) or both last
  (lane below / right) in their layers; the build says which to move. Two-way pairs are drawn
  as parallel lines. `style: "dashed"` with `dashed_means` (default "비동기·선택") for the legend.
- `groups` draw a boundary around consecutive layers (network, team, "야간 배치"); with `"tone"` it is a
  coloured dashed boundary (trust zone, 사내망). Components take a role colour from their type (system blue,
  person gray, ai purple, data green, external gray dashed); `"tone"` on a component overrides it
  (`blue` · `green` · `amber` · `purple` · `red` · `gray`).
- `steps` (≤ 6, text ≤ 40 chars): each is a `path` along existing connections (direction
  matters) or `paths` for routes at the same time. The step number rides on the first
  connection's label; the numbered step list sits under the diagram in every mode, so print,
  export and no-JS keep the story. Playback highlights one step at a time with a moving token
  and ends on the whole sequence; the caption is the `claim`. No steps → static.
- Playback (v0.13.0): each step change is choreographed by the kind (scripts/choreo.py): the previous step
  fades back, the new path, boxes and list item rise as that fade is 80% through, the token leaves with them,
  and the last 0.5 s settles into the final scene. Specs do not write cues.
- Do not draw a diagram of everything: one claim, the components it needs. Put inventories in
  a table.

## 5. Workflow

1. Start from the closest file in `examples/visuals/` (backlog, pipeline, nightly batch, incident,
   lead time, revenue, before/after steps, cloud cost, schedule, funnel, cost share, incident
   timeline, AI agent request path, RAG indexing, approval process) and replace claim, data and captions.
2. `python scripts/build_visual.py spec.json --out dist/visuals/<name> --check`
   (exit 0 = built and checked; 1 = spec, lint or gate failure; 2 = built but the browser
   gates could not run, e.g. no Playwright: say so in your report). `--font NanumGothic`
   repeats the gates under another Korean font.
3. On `FAIL spec:` fix the field named in the message. On `FAIL gate:` fix the cause
   (shorter labels or captions, fewer items, merge captions that are too close).
4. Look at `shots/<name>-715-*.png` and `-nojs-*.png` (`-360-*` too with `--phone`; the folder is cleared on
   each run). Ask: does the picture show the claim at a glance? Does every numbered row point at the part it describes? Do boxes with the same role line up (report.json
   `clutter.near_misses` should be 0 for a figure built from repeated rows)? Does every caption describe
   what is on screen at that moment — placeholders guarantee the numbers, not the story (a
   caption saying a backlog "remains" when the model drained it is caught only here)? Is
   anything shown that the text never uses? Revise the spec, rebuild.
5. Paste `macro.html` into one Confluence HTML macro per visual (each build has its own
   prefix). Animated output needs inline scripts in the target Confluence (smoke check in
   `confluence-rules.md`); otherwise rebuild with `"motion": "none"`. For slides, word
   processors or wikis that cannot embed HTML use `figure.svg` or `figure.png` (final scene with
   a source line); `preview.html` is a standalone page.
6. Report the spec, the mode (live/static), the gate result and what was not verified
   (rendering in the target Confluence).

## 6. What the gates guarantee, and what they do not

Guaranteed by `--check` (Chromium): no overlapping or clipped text at 24 moments and two
widths, no text painted over by a later shape, text contrast ≥ 4.5:1, text ≥ 9 px, height
≤ 520 px at 715 px and ≤ 600 px at 360 px, captions readable at the default speed, labels
not shown before their event, browser state equal to the model at sample times, working
controls, reduced motion, print, two independent blocks, readable no-JS figure on phones,
no external requests; text that belongs to a box stays inside it and connection labels stay
off boxes; the exported `figure.svg` has all text inside the figure, no overlap, nothing
painted over and readable contrast. Not judged: whether the visual is the right one, whether the claim is
true, whether the picture is beautiful. Step 4 is where that happens.
