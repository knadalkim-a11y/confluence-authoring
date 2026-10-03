# Document visuals from a spec (v0.9.0)

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
| a mechanism none of these express (discrete workers, retries, routing, cycles) | custom live scene, see `live-runtime.md` (thread-pool is the example) | animated |

Deliberately not offered: pie/donut, 3D, dual y-axes, KPI gauge tiles, decorative motion.
`motion: "none"` forces a static figure (use it when the target Confluence does not run inline
scripts); `"play"` animates a kind that is static by default (bars grow once).

## 3. Fields every spec has

| Field | Rule |
|---|---|
| `kind` | `flow` · `trend` · `bars` · `share` · `timeline` · `diagram` |
| `title` | Accessible name (≤ 120 chars). The page heading usually says it too. |
| `claim` | The one-sentence takeaway (≤ 120). Shown under a static figure; use it as the last caption of an animated one. |
| `source` | Where the numbers come from. Required. |
| `data_kind` | `measured` · `estimate` · `example`; for `diagram`: `current` (현재 구조) · `proposed` (제안안) · `example`. Required; shown in the picture or notes so illustrative numbers or a proposal are never mistaken for the real thing. |
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
- Picture: stages with limit, thick gauge and %; waiting requests as yellow dots (one dot = N
  requests, chosen automatically) or limit cells (one cell = one request); rejected requests
  leave in red; "한도 도달" and "여유" pills appear only while a queue exists (multi-stage).
  Two single-stage variants sit side by side with per-lane readouts and a wait-time sparkline;
  a single lane gets a "대기 추이" strip (peak labelled once reached) so the printed/no-JS
  picture still shows a backlog that drained before the end.
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
- Events: `start`, `end` and every event `label` (or `name`).
- Placeholders: `<series name>_end`, `<series name>_max` (non-word characters → `_`, e.g.
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
- `groups` draw a boundary around consecutive layers (network, team, "야간 배치").
- `steps` (≤ 6, text ≤ 40 chars): each is a `path` along existing connections (direction
  matters) or `paths` for routes at the same time. The step number rides on the first
  connection's label; the numbered step list sits under the diagram in every mode, so print,
  export and no-JS keep the story. Playback highlights one step at a time with a moving token
  and ends on the whole sequence; the caption is the `claim`. No steps → static.
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
4. Look at `shots/<name>-715-*.png`, `-360-*.png` and `-nojs-*.png` (the folder is cleared on
   each run). Ask: does the picture show the claim at a glance? Does every caption describe
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
