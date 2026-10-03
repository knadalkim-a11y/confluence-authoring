"""Spec-driven visuals for documents: a small JSON spec in, a validated Confluence macro out.

An author (person or AI) describes the situation and the data; this module validates the
spec, computes the model (queues, interpolation, events), binds captions to model events,
and returns scene data for the live JS scenes in visuals/live/scenes/ (flow, trend, bars,
timeline). Numbers shown in text come from the model through placeholders, never typed.
See references/visual-specs.md for the spec reference and selection rules.
"""
from __future__ import annotations
import datetime as dt, math, re
from monitoring_cases import (finite, fluid_tokens, first_reach, interp, token_speed, paced_rate, caption_walls,
                              caption_need, nice_max, grp, DEFAULT_SPEED)

KINDS = ('flow', 'trend', 'bars', 'share', 'timeline', 'diagram', 'distribution')
DATA_KINDS = {'measured': '측정값', 'estimate': '추정값', 'example': '예시 데이터'}
DIAGRAM_KINDS = {'current': '현재 구조', 'proposed': '제안안', 'example': '예시'}   # a diagram states a structure, not numbers
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫'
TONES = ('neutral', 'good', 'bad')
COLORS = ('blue', 'purple', 'green', 'red', 'amber', 'gray')


class SpecError(ValueError):
    pass


def need(cond, msg):
    if not cond:
        raise SpecError(msg)


def text(v, name, lo=1, hi=200):
    need(isinstance(v, str) and lo <= len(v.strip()) <= hi and '{{' not in v, f'{name}: text of {lo}-{hi} chars required')
    return v.strip()


def num(v, name, lo=-1e9, hi=1e9):
    try:
        return finite(v, name, lo, hi)
    except ValueError as e:
        raise SpecError(str(e))


def only(obj, allowed, name):
    need(isinstance(obj, dict), f'{name}: object required')
    extra = set(obj) - set(allowed)
    need(not extra, f'{name}: unknown keys {sorted(extra)} (allowed: {sorted(allowed)})')
    return obj


def fmt(v, decimals=None):
    """Readable number: thousands separators, decimals only where they carry information."""
    if decimals is None:
        decimals = 0 if abs(v) >= 100 or float(v).is_integer() else 1
    s = f'{v:,.{decimals}f}'
    return s


def decimals_of(values, cap=2):
    """Decimals the author actually used (12.8 -> 1), so shown values never round away information."""
    d = 0
    for v in values:
        s = repr(float(v))
        if 'e' not in s and '.' in s and not float(v).is_integer():
            d = max(d, len(s.split('.')[1].rstrip('0')))
    return min(d, cap)


def r1(x):
    """Round half up to 0.1, like the scenes' Math.round(x*10)/10 (Python's round() is half-even)."""
    return math.floor(x * 10 + 0.5) / 10


def fill(template, values, name):
    """Replace {key} placeholders with model values; unknown keys are errors, not blanks."""
    def rep(m):
        key = m[1]
        need(key in values, f'{name}: unknown placeholder {{{key}}}; available: {", ".join(sorted(values))}')
        return values[key]
    out = re.sub(r'\{([^{}\s]+)\}', rep, template)
    need('{' not in out and '}' not in out, f'{name}: unbalanced braces left in "{out}"')
    return out


def resolve_at(at, events, name):
    if isinstance(at, (int, float)) and not isinstance(at, bool):
        return float(at)
    need(isinstance(at, str), f'{name}: "at" must be a time or an event name')
    need(at in events, f'{name}: unknown event "{at}"; available: {", ".join(sorted(k for k, v in events.items() if v is not None))}')
    need(events[at] is not None, f'{name}: event "{at}" never happens in this model; choose another or change the data')
    return float(events[at])


def captions_from(spec, events, values, end, name='captions'):
    raw = spec.get('captions') or []
    need(isinstance(raw, list), f'{name}: list required')
    out = []
    for i, c in enumerate(raw):
        only(c, ('at', 'text'), f'{name}[{i}]')
        t = resolve_at(c.get('at', 0), events, f'{name}[{i}]')
        need(0 <= t <= end + 1e-9, f'{name}[{i}]: time {t:g} outside 0..{end:g}')
        out.append([round(t, 6), '', fill(text(c.get('text'), f'{name}[{i}].text', 2, 120), values, f'{name}[{i}].text')])
    out.sort(key=lambda c: c[0])
    for i, c in enumerate(out):
        c[1] = CIRCLED[i] if i < len(CIRCLED) else f'{i + 1}.'
    return out


def common(spec):
    kind = spec.get('kind')
    need(kind in KINDS, f'kind must be one of {KINDS}')
    title = text(spec.get('title'), 'title', 2, 120)
    claim = text(spec.get('claim'), 'claim', 2, 120)
    source = text(spec.get('source'), 'source (where the numbers come from)', 2, 400)
    data_kind = spec.get('data_kind')
    if kind == 'diagram':
        need(data_kind in DIAGRAM_KINDS, f'data_kind must be one of {list(DIAGRAM_KINDS)} (say whether this is the current structure or a proposal)')
    else:
        need(data_kind in DATA_KINDS, f'data_kind must be one of {list(DATA_KINDS)} (say whether numbers are real)')
    motion = spec.get('motion', 'auto')
    need(motion in ('auto', 'play', 'none'), 'motion must be auto, play or none')
    return kind, title, claim, source, data_kind, motion


# ---------------------------------------------------------------- flow
def schedule_rate(sched, t):
    r = sched[0][1]
    for a, v in sched:
        if t >= a - 1e-10:
            r = v
    return r


def fluid_schedule(sched, capacity, horizon, limit=None, steps=200):
    """Deterministic fluid queue in front of one bottleneck. Inflow is piecewise constant;
    same integration as monitoring_cases.fluid_queue (change instants included exactly)."""
    times = sorted(set([i * horizon / steps for i in range(steps + 1)] + [a for a, _ in sched if 0 < a < horizon]))
    q = inc = out = rej = 0.0
    r0 = schedule_rate(sched, 0)
    rows = [dict(t=0, rate=r0, served_rate=min(r0, capacity), q=0, incoming=0, served=0, rejected=0)]
    for t0, t1 in zip(times, times[1:]):
        rate = schedule_rate(sched, t0); d = t1 - t0; incoming = rate * d
        served = min(q + incoming, capacity * d); q += incoming - served
        rejected = max(0, q - limit) if limit is not None else 0; q -= rejected
        inc += incoming; out += served; rej += rejected
        rows.append(dict(t=t1, rate=rate, served_rate=served / d, q=round(q, 9), incoming=round(inc, 9), served=round(out, 9), rejected=round(rej, 9)))
    return rows


def flow_lane_model(sched, stages, limit, horizon):
    caps = [s['capacity'] for s in stages]
    b = min(range(len(caps)), key=lambda i: (caps[i], i))
    peak = max(r for _, r in sched)
    for i in range(b):
        need(caps[i] >= peak, f'stage "{stages[i]["name"]}" ({fmt(caps[i])}) is below peak inflow ({fmt(peak)}): '
                              'the queue would form there first. Make it the bottleneck or raise its capacity.')
    rows = fluid_schedule(sched, caps[b], horizon, limit)
    S = dict(t=[round(r['t'], 6) for r in rows], q=[round(r['q'], 6) for r in rows], inc=[round(r['incoming'], 6) for r in rows],
             srv=[round(r['served'], 6) for r in rows], rej=[round(r['rejected'], 6) for r in rows])
    return b, rows, S


def flow_events(S, cap, limit, sched, horizon, lane):
    ev = {}
    t, q = S['t'], S['q']
    onset = next((t[i] for i in range(len(q)) if q[i] > 1e-9), None)
    ev['queue'] = onset
    if onset is not None:
        k = t.index(onset)
        ev['drain'] = next((t[i] for i in range(k, len(q)) if q[i] <= 1e-9), None)
        peak = max(q); ev['peak'] = t[q.index(peak)]
    else:
        ev['drain'] = ev['peak'] = None
    ev['full'] = first_reach(t, q, limit - 1e-9) if limit is not None and max(q) >= limit - 1e-6 else None
    for x in (0.5, 1, 2, 3, 5, 10):
        ev[f'wait:{x:g}'] = first_reach(t, q, cap * x) if max(q) >= cap * x - 1e-9 else None
    return {k if lane == 0 else f'{k}@{lane}': v for k, v in ev.items()}


def lane_note(l, rate_u, count_u):
    s = f'{l["name"] + ": " if l["name"] else ""}병목 {l["stages"][l["b"]]["name"]} 한도 {fmt(l["stages"][l["b"]]["capacity"])}{rate_u}'
    return s + (f', 대기 상한 {fmt(l["limit"])}{count_u}' if l['limit'] else '')


def flow_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'inflow', 'stages', 'queue', 'variants',
                'units', 'labels', 'captions', 'callouts'), 'flow spec')
    tm = only(spec.get('time'), ('unit', 'end'), 'time')
    tu = text(tm.get('unit'), 'time.unit', 1, 4); end = num(tm.get('end'), 'time.end', 0.1, 10000)
    un = only(spec.get('units') or {}, ('rate', 'count'), 'units')
    rate_u = text(un.get('rate', f'건/{tu}'), 'units.rate', 1, 10); count_u = text(un.get('count', '건'), 'units.count', 1, 6)
    raw = spec.get('inflow'); need(isinstance(raw, list) and 1 <= len(raw) <= 8, 'inflow: list of [time, rate] (1-8 steps)')
    sched = []
    for i, x in enumerate(raw):
        need(isinstance(x, list) and len(x) == 2, f'inflow[{i}]: [time, rate]')
        sched.append([num(x[0], f'inflow[{i}] time', 0, end), num(x[1], f'inflow[{i}] rate', 0, 1e7)])
    need(sched[0][0] == 0 and all(a[0] < b[0] for a, b in zip(sched, sched[1:])), 'inflow: first time 0, times increasing')
    def parse_stages(raw, name):
        need(isinstance(raw, list) and 1 <= len(raw) <= 4, f'{name}: 1-4 stages')
        out = []
        for i, s in enumerate(raw):
            only(s, ('name', 'short', 'capacity'), f'{name}[{i}]')
            nm = text(s.get('name'), f'{name}[{i}].name', 1, 14)
            need('short' in s or len(nm) <= 8, f'{name}[{i}]: names longer than 8 chars need a "short" label for narrow screens')
            out.append(dict(name=nm, short=text(s.get('short', nm), f'{name}[{i}].short', 1, 8),
                            capacity=num(s.get('capacity'), f'{name}[{i}].capacity', 1e-6, 1e7)))
        return out
    base_stages = parse_stages(spec.get('stages'), 'stages')
    qspec = only(spec.get('queue') or {}, ('limit',), 'queue')
    base_limit = None if qspec.get('limit') is None else num(qspec['limit'], 'queue.limit', 1, 40)
    variants = spec.get('variants') or [{}]
    need(isinstance(variants, list) and 1 <= len(variants) <= 2, 'variants: 1 or 2 (side by side)')
    lanes, values, events = [], {}, {'start': 0.0, 'end': end}
    for i, (a, _) in enumerate(sched[1:], 1):
        events[f'change' if i == 1 else f'change:{i}'] = a
    for li, v in enumerate(variants):
        only(v, ('name', 'tone', 'capacity', 'limit'), f'variants[{li}]')
        stages = [dict(s) for s in base_stages]
        lim = base_limit
        if 'limit' in v:
            lim = None if v['limit'] is None else num(v['limit'], f'variants[{li}].limit', 1, 40)
        b0 = min(range(len(stages)), key=lambda i: (stages[i]['capacity'], i))
        if 'capacity' in v:
            stages[b0]['capacity'] = num(v['capacity'], f'variants[{li}].capacity', 1e-6, 1e7)
        b, rows, S = flow_lane_model(sched, stages, lim, end)
        cap = stages[b]['capacity']
        events.update(flow_events(S, cap, lim, sched, end, li))
        sfx = '' if li == 0 else f'@{li}'
        q_end, srv_end, rej_end = S['q'][-1], S['srv'][-1], S['rej'][-1]
        over_t = next((a for a, r in sched if r > cap), None)
        over_in = S['inc'][-1] - interp(S['t'], S['inc'], over_t) if over_t is not None else 0
        values.update({f'queue_end{sfx}': grp(q_end), f'served_end{sfx}': grp(srv_end), f'rejected_end{sfx}': grp(rej_end),
                       f'wait_end{sfx}': fmt(q_end / cap, 1), f'capacity{sfx}': fmt(cap), f'bottleneck{sfx}': stages[b]['name'],
                       f'reject_rate{sfx}': fmt(100 * rej_end / over_in if over_in else 0, 1), f'limit{sfx}': fmt(lim) if lim else '-',
                       f'limit_wait{sfx}': fmt(lim / cap, 2) if lim else '-', f'limit_wait_ms{sfx}': f'{lim / cap * 1000:.0f}' if lim else '-',
                       f'excess{sfx}': fmt(max(0, max(r for _, r in sched) - cap))})
        name = text(v.get('name', ''), f'variants[{li}].name', 1, 30) if len(variants) > 1 else ''
        tone = v.get('tone', 'neutral'); need(tone in TONES, f'variants[{li}].tone: {TONES}')
        lanes.append(dict(name=name, tone=tone, stages=stages, b=b, limit=lim, rows=rows, S=S))
    peak = max(r for _, r in sched)
    values.update({f't_{k}': fmt(v, 1) for k, v in events.items() if v is not None})   # event times, e.g. {t_drain}
    values.update(inflow_start=fmt(sched[0][1]), inflow_peak=fmt(peak), inflow_end=fmt(sched[-1][1]), end=fmt(end), time_unit=tu,
                  rate_unit=rate_u, count_unit=count_u, change=fmt(sched[1][0]) if len(sched) > 1 else '-')
    captions = captions_from(spec, events, values, end)
    unit = 1
    for u in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):   # <= ~25 tokens per wall second at ~10 s plays
        unit = u
        if peak / u * end / 10 <= 25:
            break
    lb = only(spec.get('labels') or {}, ('inflow', 'served', 'wait', 'spare', 'limit_pill', 'limit_tag', 'history'), 'labels')
    labels = dict(history=lb.get('history', '대기 추이'), inflow=lb.get('inflow', '유입'), served=lb.get('served', '처리'), wait=lb.get('wait', '새 요청 대기'),
                  spare=lb.get('spare', '여유'), limit_pill=lb.get('limit_pill', '한도 도달'), limit_tag=lb.get('limit_tag', '상한 {limit}'),
                  rate_unit=rate_u, count_unit=count_u, time_unit=tu, data_kind=DATA_KINDS[data_kind])
    legend = []   # dot scale lives in the notes: the count label carries the number, as in the article demos
    if len(lanes) > 1:
        legend.append('아래 선 = 대기 시간')
    legend.append(DATA_KINDS[data_kind])
    labels['legend'] = ' · '.join(legend)
    callouts = []
    for i, c in enumerate(spec.get('callouts') or []):
        only(c, ('lane', 'at', 'text', 'tone'), f'callouts[{i}]')
        lane = c.get('lane', 0); need(lane in range(len(lanes)), f'callouts[{i}].lane: 0..{len(lanes) - 1}')
        need(c.get('tone', 'info') in ('ok', 'warn', 'hot', 'info'), f'callouts[{i}].tone: ok|warn|hot|info')
        callouts.append([lane, resolve_at(c.get('at', 0), events, f'callouts[{i}]'), text(fill(text(c.get('text'), f'callouts[{i}].text', 1, 80), values, f'callouts[{i}]'), f'callouts[{i}].text (after placeholders)', 1, 24), c.get('tone', 'info')])
    base = [[0, 1.0 * end / 10]]
    live = motion == 'play' or (motion == 'auto' and len(captions) >= 2)
    if not captions:
        captions = [[end, '', claim]]
    rate = paced_rate(captions, end, base) if live else [[0, 1]]
    t = lanes[0]['S']['t']
    data = dict(scene='flow', time=dict(unit=tu, end=end), inflow=sched, unit=unit, speed=token_speed(peak, unit), labels=labels,
                captions=captions, rate=rate, callouts=callouts, t=t,
                axes=dict(wait_max=nice_max(max(max(l['S']['q']) / l['stages'][l['b']]['capacity'] for l in lanes) or 1)),
                lanes=[dict(name=l['name'], tone=l['tone'], b=l['b'], limit=l['limit'], peak_q=max(l['S']['q']),
                            peak_t=l['S']['t'][l['S']['q'].index(max(l['S']['q']))],
                            stages=[dict(name=s['name'], short=s['short'], cap=s['capacity']) for s in l['stages']],
                            q=l['S']['q'], srv=l['S']['srv'], rej=l['S']['rej'], inc=l['S']['inc'], tokens=fluid_tokens(l['S'], unit)) for l in lanes])
    aria = f'{title}. {claim}'
    notes = (f'출처: {source} ({DATA_KINDS[data_kind]}). 결정론적 유체 모델: 유입 {" → ".join(f"{fmt(r)}{rate_u}({fmt(a)}{tu}~)" for a, r in sched)}, '
             + '; '.join(lane_note(l, rate_u, count_u) for l in lanes)
             + f'. 대기는 구간별 수지(유입−처리)의 적분, 새 요청 대기 시간 = 대기 ÷ 병목 한도(FIFO). 점 1개 = {grp(unit)}{count_u}.')
    head = ['시각'] + [f'{(l["name"] + " ") if l["name"] else ""}대기' for l in lanes] + ['누적 처리'] + (['누적 거부'] if any(l['limit'] for l in lanes) else [])
    step = max(1, len(t) // 20)
    rows = [[fmt(t[i], 2)] + [grp(l['S']['q'][i]) for l in lanes] + [grp(lanes[-1]['S']['srv'][i])] + ([grp(lanes[-1]['S']['rej'][i])] if any(l['limit'] for l in lanes) else [])
            for i in range(0, len(t), step)]
    def expect(T):
        st = {'queue': [r1(max(0, interp(t, l['S']['q'], T))) for l in lanes], 'rejected': [r1(max(0, interp(t, l['S']['rej'], T))) for l in lanes]}
        stats = []
        if len(lanes) == 1:
            l = lanes[0]; cap = l['stages'][l['b']]['capacity']; i = next((k for k in range(1, len(t)) if t[k] > T + 1e-9), len(t) - 1)
            served = (l['S']['srv'][i] - l['S']['srv'][i - 1]) / (t[i] - t[i - 1])
            stats = [grp(schedule_rate(sched, T)), grp(served), f'{max(0, interp(t, l["S"]["q"], T)) / cap:.1f}']   # same formatting as the scene
        return dict(state=st, stats=stats)
    ann = [[c[2], c[1]] for c in callouts]
    if len(lanes) == 1 and max(lanes[0]['S']['q']) > 1e-6 and lanes[0]['S']['q'][-1] < 1e-6:   # history strip only when the backlog drained
        qq = lanes[0]['S']['q']; ann.append([f'최대 {grp(max(qq))}{count_u}', lanes[0]['S']['t'][qq.index(max(qq))]])
    samples = sorted({round(x, 4) for x in [0.05 * end] + [c[0] + 0.03 * end for c in captions if c[0] + 0.03 * end < end] + [end]})[:6]
    while len(samples) < 6:
        samples = sorted(set(samples + [round(end * (len(samples) + 1) / 7, 4)]))
    samples = samples[:5] + [end] if end not in samples[:6] else samples[:6]   # the final state is always gated
    checks = dict(end=end, samples=samples, annotations=[[a, round(b, 6)] for a, b in ann if 0 < b < end], expect=expect, resize_at=round(end / 2, 4))
    table = (head, rows)
    numeric = dict(lanes=[dict(name=l['name'], queue_end=l['S']['q'][-1], served_end=l['S']['srv'][-1], rejected_end=l['S']['rej'][-1]) for l in lanes],
                   events={k: v for k, v in events.items() if v is not None}, unit=unit)
    return dict(data=data, aria=aria, notes=notes, table=table, checks=checks, live=live, numeric=numeric, title=title)


# ---------------------------------------------------------------- trend
def trend_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'groups', 'panels', 'events', 'thresholds', 'captions',
                'bands', 'annotations', 'between', 'stream', 'log'), 'trend spec')
    tm = only(spec.get('time'), ('unit', 'end', 'ticks', 'start'), 'time')
    tu = text(tm.get('unit'), 'time.unit', 1, 4); end = num(tm.get('end'), 'time.end', 1e-6, 1e7); start = num(tm.get('start', 0), 'time.start', -1e7, end)
    need(start == 0, 'time.start must be 0 (shift your time values)')
    groups_raw = spec.get('groups') or [dict(panels=spec.get('panels'))]
    need(isinstance(groups_raw, list) and 1 <= len(groups_raw) <= 4, 'groups: 1-4 (4 make a 2 x 2 grid)')
    events, values, groups = {'start': 0.0, 'end': end}, {'end': fmt(end), 'time_unit': tu}, []
    for e in spec.get('events') or []:
        only(e, ('at', 'label', 'name', 'color'), 'events[]')
        need(e.get('color', 'gray') in COLORS, f'events[].color: one of {COLORS}')
        nm = e.get('name') or e.get('label'); events[nm] = num(e.get('at'), f'event {nm}', 0, end)
    for gi, g in enumerate(groups_raw):
        only(g, ('name', 'title', 'color', 'pill', 'note', 'panels', 'events'), f'groups[{gi}]')
        for e in g.get('events') or []:   # events of one column only (scenario A / B)
            only(e, ('at', 'label', 'name', 'color'), f'groups[{gi}].events[]')
            need(e.get('color', 'gray') in COLORS, f'groups[{gi}].events[].color: one of {COLORS}')
            nm = e.get('name') or e.get('label'); events[nm if gi == 0 else f'{nm}@{gi}'] = num(e.get('at'), f'event {nm}', 0, end)
        need(g.get('color', 'gray') in COLORS, f'groups[{gi}].color: one of {COLORS}')
        panels = []
        need(isinstance(g.get('panels'), list) and 1 <= len(g['panels']) <= 4, f'groups[{gi}].panels: 1-4 panels')
        for pi, p in enumerate(g['panels']):
            only(p, ('label', 'unit', 'max', 'ticks', 'series', 'decimals', 'hide_label'), f'groups[{gi}].panels[{pi}]')
            series = []
            need(isinstance(p.get('series'), list) and 1 <= len(p['series']) <= 3, f'panel {pi}: 1-3 series')
            for si, s in enumerate(p['series']):
                only(s, ('name', 'color', 'points', 'style', 'dots', 'area', 'label'), f'panel {pi} series {si}')
                need(s.get('style', 'solid') in ('solid', 'dashed'), f'series {si}.style: solid or dashed')
                pts = s.get('points'); need(isinstance(pts, list) and 2 <= len(pts) <= 2000, f'series {si}: 2-2000 [t, v] points')
                pts = [[num(a, 'time', 0, end), num(b, 'value')] for a, b in pts]
                need(all(a[0] < b[0] for a, b in zip(pts, pts[1:])), f'series {si}: times increasing')
                need(pts[0][0] >= 0 and pts[-1][0] <= end + 1e-9, f'series {si}: points within 0..{end:g}')   # a series may cover part of the axis
                color = s.get('color', COLORS[si]); need(color in COLORS, f'series {si}: color in {COLORS}')
                series.append(dict(name=text(s.get('name'), 'series.name', 1, 20), color=color, t=[x[0] for x in pts], v=[x[1] for x in pts],
                                   dashed=s.get('style') == 'dashed', dots=bool(s.get('dots')), area=s.get('area', True) is not False, label=s.get('label', True) is not False))
                key = re.sub(r'\W+', '_', series[-1]['name']).strip('_') or f's{si}'
                values[f'{key}_end' + (f'@{gi}' if gi else '')] = fmt(pts[-1][1], p.get('decimals'))
                values[f'{key}_max' + (f'@{gi}' if gi else '')] = fmt(max(x[1] for x in pts), p.get('decimals'))
                values[f'{key}_start' + (f'@{gi}' if gi else '')] = fmt(pts[0][1], p.get('decimals'))
                if pts[0][1]:
                    values[f'{key}_change_pct' + (f'@{gi}' if gi else '')] = f'{(pts[-1][1] - pts[0][1]) / abs(pts[0][1]) * 100:+.0f}'
            vmax = p.get('max', nice_max(max(max(s['v']) for s in series)))
            unit = text(p.get('unit', ''), 'unit', 0, 6) if p.get('unit') else ''
            ticks = p.get('ticks') or [vmax, vmax / 2, 0]
            dec = p.get('decimals') if p.get('decimals') is not None else decimals_of([v for s in series for v in s['v']], 1)
            panels.append(dict(label=text(p.get('label'), 'panel.label', 1, 24), hide=bool(p.get('hide_label')), unit=unit, max=num(vmax, 'max', 1e-9), series=series,
                               ticks=[num(x, 'tick') for x in ticks], decimals=dec))
        def timed(lst, name, ln):
            out = []
            for i, x in enumerate(lst or []):
                need(isinstance(x, list) and len(x) == 3, f'{name}[{i}]: [at, text, tone]')
                need(x[2] in ('ok', 'warn', 'hot', 'info', 'bad', 'purple'), f'{name}[{i}] tone: ok|warn|hot|info|bad|purple')
                out.append([resolve_at(x[0], events, name), fill(text(x[1], name, 1, ln), values, name), x[2]])
            return sorted(out, key=lambda x: x[0])
        gev = [[events[(e.get('name') or e.get('label')) if gi == 0 else f"{e.get('name') or e.get('label')}@{gi}"], text(e.get('label'), 'event label', 1, 16), e.get('color', 'gray')] for e in g.get('events') or []]
        groups.append(dict(events=gev, name=g.get('name', ''), title=text(g['title'], f'groups[{gi}].title', 1, 24) if g.get('title') else '', color=g.get('color', 'gray'), pill=timed(g.get('pill'), f'groups[{gi}].pill', 24), note=timed(g.get('note'), f'groups[{gi}].note', 30), panels=panels))
    thresholds = []
    for i, th in enumerate(spec.get('thresholds') or []):
        only(th, ('panel', 'value', 'label'), f'thresholds[{i}]')
        thresholds.append([text(th.get('panel'), 'thresholds.panel', 1, 24), num(th.get('value'), 'thresholds.value'), text(th.get('label'), 'thresholds.label', 1, 20)])
    ev_marks = [[events[e.get('name') or e.get('label')], text(e.get('label'), 'event label', 1, 16), e.get('color', 'gray')] for e in spec.get('events') or []]
    for k, v in events.items():
        values.setdefault(f't_{k}', fmt(v))
    panel_of = {p['label']: p for g in groups for p in g['panels']}
    def series_of(pl, nm, where):
        need(pl in panel_of, f'{where}.panel: one of {list(panel_of)}')
        ss = [x for x in panel_of[pl]['series'] if x['name'] == nm]
        need(ss, f'{where}.series: one of {[x["name"] for x in panel_of[pl]["series"]]}')
        return ss[0]
    bands = []   # shaded interval with a bracket label; {duration} is computed
    for i, b in enumerate(spec.get('bands') or []):
        only(b, ('from', 'to', 'label', 'color'), f'bands[{i}]')
        a0, a1 = resolve_at(b.get('from'), events, f'bands[{i}].from'), resolve_at(b.get('to'), events, f'bands[{i}].to')
        need(a0 < a1, f'bands[{i}]: from < to'); need(b.get('color', 'amber') in COLORS, f'bands[{i}].color: one of {COLORS}')
        lab = text(fill(text(b.get('label'), f'bands[{i}].label', 1, 60), dict(values, duration=fmt(a1 - a0) + tu), f'bands[{i}].label'), f'bands[{i}].label', 1, 20)
        bands.append([a0, a1, lab, b.get('color', 'amber')])
    need(len(bands) <= 3, 'bands: at most 3')
    notes_on = []   # text placed at a series value, shown from its time on
    for i, a in enumerate(spec.get('annotations') or []):
        only(a, ('at', 'panel', 'series', 'text', 'color', 'side'), f'annotations[{i}]')
        sr = series_of(a.get('panel'), a.get('series'), f'annotations[{i}]'); at = resolve_at(a.get('at'), events, f'annotations[{i}].at')
        need(a.get('color', 'red') in COLORS and a.get('side', 'above') in ('above', 'below'), f'annotations[{i}]: color in {COLORS}, side above|below')
        tx = text(fill(text(a.get('text'), f'annotations[{i}].text', 1, 80), values, f'annotations[{i}].text'), f'annotations[{i}].text (after placeholders)', 1, 28)
        notes_on.append([at, a['panel'], a['series'], tx, a.get('color', 'red'), a.get('side', 'above')])
    need(len(notes_on) <= 6, 'annotations: at most 6')
    between = []   # area between two series of one panel
    for i, b in enumerate(spec.get('between') or []):
        only(b, ('panel', 'upper', 'lower', 'from', 'to', 'color'), f'between[{i}]')
        series_of(b.get('panel'), b.get('upper'), f'between[{i}]'); series_of(b.get('panel'), b.get('lower'), f'between[{i}]')
        a0, a1 = resolve_at(b.get('from', 0), events, f'between[{i}].from'), resolve_at(b.get('to', 'end'), events, f'between[{i}].to')
        need(b.get('color', 'red') in COLORS, f'between[{i}].color')
        between.append([b['panel'], b['upper'], b['lower'], a0, a1, b.get('color', 'red')])
    stream = None   # a row of requests between two panels; a share of them is diverted (fails, or goes to a side box)
    if spec.get('stream'):
        st = only(spec['stream'], ('after', 'label', 'box', 'side', 'phases', 'end_note'), 'stream')
        need(st.get('after') in panel_of, f'stream.after: one of {list(panel_of)}')
        ph = []
        for i, x in enumerate(st.get('phases') or []):
            only(x, ('from', 'divert', 'color', 'divert_color', 'note'), f'stream.phases[{i}]')
            need(x.get('color', 'blue') in COLORS and x.get('divert_color', 'red') in COLORS, f'stream.phases[{i}]: colors in {COLORS}')
            ph.append([resolve_at(x.get('from', 0), events, f'stream.phases[{i}].from'), num(x.get('divert', 0), f'stream.phases[{i}].divert', 0, 1),
                       x.get('color', 'blue'), x.get('divert_color', 'red'), fill(text(x['note'], f'stream.phases[{i}].note', 1, 60), values, 'note') if x.get('note') else ''])
        need(ph and ph[0][0] == 0, 'stream.phases: the first phase starts at 0')
        stream = dict(after=st['after'], label=text(st.get('label', '요청'), 'stream.label', 1, 6), box=text(st['box'], 'stream.box', 1, 10) if st.get('box') else '',
                      side=text(st['side'], 'stream.side', 1, 8) if st.get('side') else '', phases=sorted(ph), end_note=text(st['end_note'], 'stream.end_note', 1, 24) if st.get('end_note') else '')
    log = None   # log lines under the panels, each shown from its time on; 'hot' lines are the culprit
    if spec.get('log'):
        lg = only(spec['log'], ('label', 'lines'), 'log')
        lines = []
        for i, x in enumerate(lg.get('lines') or []):
            need(isinstance(x, list) and len(x) in (2, 3), f'log.lines[{i}]: [at, text] or [at, text, "hot"]')
            lines.append([resolve_at(x[0], events, f'log.lines[{i}]'), text(x[1], f'log.lines[{i}]', 1, 70), len(x) == 3 and x[2] == 'hot'])
        need(1 <= len(lines) <= 8, 'log.lines: 1-8 lines')
        log = dict(label=text(lg.get('label', '로그'), 'log.label', 1, 16), lines=sorted(lines, key=lambda x: x[0]))
    captions = captions_from(spec, events, values, end)
    auto = not tm.get('ticks')
    ticks = tm.get('ticks') or [[x, fmt(x)] for x in (0, end / 2, end)]
    ticks = [[num(a, 'tick'), text(str(b), 'tick label', 1, 10)] for a, b in ticks]
    if auto:   # only generated numeric ticks get the unit; author labels stay as written
        ticks[-1][1] += tu
    live = motion == 'play' or (motion == 'auto' and len(captions) >= 2)
    if not captions:
        captions = [[end, '', claim]]
    rate = paced_rate(captions, end, [[0, end / 12]]) if live else [[0, 1]]
    data = dict(scene='trend', time=dict(unit=tu, end=end), groups=groups, thresholds=thresholds, events=ev_marks, ticks=ticks,
                bands=bands, annotations=notes_on, between=between, stream=stream, log=log,
                captions=captions, rate=rate, labels=dict(data_kind=DATA_KINDS[data_kind]))
    def expect(T):
        return dict(state={'values': [[[r1(interp(s['t'], s['v'], T)) for s in p['series']] for p in g['panels']] for g in groups]}, stats=[])
    ann = ([[x[1], x[0]] for g in groups for x in g['pill'] + g['note'] if 0 < x[0] < end] + [[lb, at] for at, lb, _ in ev_marks if 0 < at < end]
           + [[x[3], x[0]] for x in notes_on if 0 < x[0] < end] + [[b[2], b[1]] for b in bands if 0 < b[1] < end]
           + [[e[1], e[0]] for g in groups for e in g['events'] if 0 < e[0] < end])
    samples = sorted({round(x, 4) for x in [0.05 * end] + [c[0] + 0.03 * end for c in captions if c[0] + 0.03 * end < end] + [end]})
    while len(samples) < 6:
        samples = sorted(set(samples + [round(end * (len(samples) + 1) / 7, 4)]))
    checks = dict(end=end, samples=samples[:6] if end in samples[:6] else samples[:5] + [end], annotations=ann, expect=expect, resize_at=round(end / 2, 4))
    notes = f'출처: {source} ({DATA_KINDS[data_kind]}). 가로축은 {tu} 단위 시간입니다.'
    head = ['시각'] + [f'{p["label"]} · {s["name"]}' for g in groups for p in g['panels'] for s in p['series']]
    grid = sorted({x for g in groups for p in g['panels'] for s in p['series'] for x in s['t']})
    step = max(1, len(grid) // 20)
    rows = [[fmt(T, 2)] + [fmt(interp(s['t'], s['v'], T), p['decimals']) for g in groups for p in g['panels'] for s in p['series']] for T in grid[::step]]
    return dict(data=data, aria=f'{title}. {claim}', notes=notes, table=(head, rows), checks=checks, live=live, numeric=dict(values=values), title=title)


# ---------------------------------------------------------------- bars
def bars_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'unit', 'items', 'highlight', 'target', 'better',
                'decimals', 'max', 'pair_labels', 'flat_pct', 'mode', 'drop'), 'bars spec')
    mode = spec.get('mode', 'compare'); need(mode in ('compare', 'funnel'), 'mode: compare|funnel')
    unit = text(spec.get('unit', ''), 'unit', 0, 8) if spec.get('unit') else ''
    items = spec.get('items'); need(isinstance(items, list) and 1 <= len(items) <= 12, 'items: 1-12')
    paired = any('before' in i for i in items)
    out = []
    for i, it in enumerate(items):
        if paired:
            only(it, ('label', 'before', 'after'), f'items[{i}]')
            out.append(dict(label=text(it.get('label'), f'items[{i}].label', 1, 16), before=num(it.get('before'), 'before', 0), after=num(it.get('after'), 'after', 0)))
        else:
            only(it, ('label', 'value'), f'items[{i}]')
            out.append(dict(label=text(it.get('label'), f'items[{i}].label', 1, 16), value=num(it.get('value'), 'value', 0)))
    better = spec.get('better', 'higher'); need(better in ('higher', 'lower'), 'better: higher|lower')
    funnel = None
    if mode == 'funnel':
        need(not paired and len(out) >= 2, 'funnel: 2-12 steps with "value"')
        vals = [x['value'] for x in out]
        need(vals[0] > 0 and all(b <= a for a, b in zip(vals, vals[1:])), 'funnel: each step must be <= the previous one (a step that grows is not a funnel)')
        conv = [None] + [b / a * 100 if a else 0 for a, b in zip(vals, vals[1:])]
        lost = [None] + [a - b for a, b in zip(vals, vals[1:])]
        basis = spec.get('drop', 'rate'); need(basis in ('rate', 'count'), 'drop: rate (lowest conversion) or count (most people lost)')
        worst = min(range(1, len(vals)), key=lambda i: (conv[i], i)) if basis == 'rate' else max(range(1, len(vals)), key=lambda i: (lost[i], -i))
        funnel = dict(conv=conv, lost=lost, worst=worst, basis=basis, overall=vals[-1] / vals[0] * 100)
    hl = spec.get('highlight') or []; need(all(h in [x['label'] for x in out] for h in hl), 'highlight: labels must match items')
    tgt = None
    if spec.get('target'):
        t = only(spec['target'], ('value', 'label'), 'target'); tgt = [num(t.get('value'), 'target.value', 0), text(t.get('label'), 'target.label', 1, 20)]
    vmax = spec.get('max') or nice_max(max([x.get('value', 0) for x in out] + [x.get('before', 0) for x in out] + [x.get('after', 0) for x in out] + ([tgt[0]] if tgt else [])))
    pl = spec.get('pair_labels') or ['이전', '이후']
    dec = spec.get('decimals')
    if dec is None:
        dec = decimals_of([x.get(k) for x in out for k in ('value', 'before', 'after') if k in x])
    flat = num(spec.get('flat_pct', 0), 'flat_pct', 0, 50)
    live = motion == 'play'
    captions = [[1.0, '', claim]]
    data = dict(scene='bars', time=dict(unit='', end=1.0), items=out, paired=paired, unit=unit, highlight=hl, target=tgt, max=vmax,
                better=better, pair_labels=pl, decimals=dec, flat_pct=flat, funnel=funnel, captions=captions, rate=[[0, 0.35]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    if funnel:
        head = ['단계', '값', '이전 단계 대비', '이탈', '처음 대비']
        rows = [[x['label'], fmt(x['value'], dec), '-' if i == 0 else fmt(funnel['conv'][i], 1) + '%', '-' if i == 0 else fmt(funnel['lost'][i], dec), fmt(x['value'] / out[0]['value'] * 100, 1) + '%'] for i, x in enumerate(out)]
        return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}). 단위: {unit or "-"}. 전환율 = 해당 단계 ÷ 이전 단계.',
                    table=(head, rows), checks=dict(end=1.0, samples=[1.0] * 6, annotations=[], expect=None, resize_at=0.5), live=live, numeric=dict(items=out, funnel=funnel), title=title)
    head = ['항목'] + ([pl[0], pl[1], '변화'] if paired else ['값'])
    rows = [[x['label'], fmt(x['before'], dec), fmt(x['after'], dec), (fmt(100 * (x['after'] - x['before']) / x['before'], 1) + '%') if x['before'] else '-']
            if paired else [x['label'], fmt(x['value'], dec)] for x in out]
    checks = dict(end=1.0, samples=[0.3, 0.6, 1.0, 1.0, 1.0, 1.0], annotations=[], expect=None, resize_at=0.5)
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}). 단위: {unit or "-"}.',
                table=(head, rows), checks=checks, live=live, numeric=dict(items=out), title=title)


# ---------------------------------------------------------------- share
def share_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'categories', 'rows', 'unit', 'highlight', 'decimals'), 'share spec')
    cats = spec.get('categories'); need(isinstance(cats, list) and 2 <= len(cats) <= 6, 'categories: 2-6 names')
    cats = [text(c, f'categories[{i}]', 1, 12) for i, c in enumerate(cats)]
    rows = spec.get('rows'); need(isinstance(rows, list) and 1 <= len(rows) <= 4, 'rows: 1-4 (e.g. 작년, 올해)')
    unit = spec.get('unit', '%')
    out = []
    for i, r in enumerate(rows):
        only(r, ('label', 'values'), f'rows[{i}]')
        vals = r.get('values'); need(isinstance(vals, list) and len(vals) == len(cats), f'rows[{i}].values: one value per category ({len(cats)})')
        vals = [num(v, f'rows[{i}].values', 0) for v in vals]; tot = sum(vals); need(tot > 0, f'rows[{i}]: values sum to 0')
        if unit == '%':
            need(abs(tot - 100) <= 1.0, f'rows[{i}]: percentages add to {tot:g}, not 100 (give raw values with another unit to normalise)')
        out.append(dict(label=text(r.get('label'), f'rows[{i}].label', 1, 10), raw=vals, pct=[v / tot * 100 for v in vals]))
    hl = spec.get('highlight')
    need(hl is None or hl in cats, 'highlight: one of the categories')
    h = cats.index(hl) if hl else -1
    dec = spec.get('decimals', decimals_of([v for r in out for v in r['raw']] if unit == '%' else [0]))
    change = None
    if h >= 0 and len(out) >= 2:
        a, b = out[0]['pct'][h], out[-1]['pct'][h]
        change = f'{cats[h]} {fmt(a, dec)}% → {fmt(b, dec)}% ({"+" if b >= a else "−"}{fmt(abs(b - a), dec)}%p)'
    data = dict(scene='share', time=dict(unit='', end=1.0), categories=cats, rows=out, highlight=h, decimals=dec, change=change,
                captions=[[1.0, '', claim]], rate=[[0, 1]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    head = ['구분'] + cats
    trows = [[r['label']] + [fmt(p, dec) + '%' + ('' if unit == '%' else f' ({fmt(v)}{unit})') for p, v in zip(r['pct'], r['raw'])] for r in out]
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}). 각 막대는 100%입니다.', table=(head, trows),
                checks=dict(end=1.0, samples=[1.0] * 6, annotations=[], expect=None, resize_at=0.5), live=False, numeric=dict(rows=out), title=title)


# ---------------------------------------------------------------- timeline
CLOCK = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')


def as_day(v, name, origin, clock=None):
    """Days from a date origin, minutes for HH:MM clock times (after midnight wraps), or a number."""
    if isinstance(v, str) and clock is not None:
        m = CLOCK.match(v); need(m, f'{name}: HH:MM like the time range')
        x = int(m[1]) * 60 + int(m[2])
        return x + 1440 if x < clock else x
    if isinstance(v, str):
        try:
            d = dt.date.fromisoformat(v)
        except ValueError:
            raise SpecError(f'{name}: ISO date YYYY-MM-DD or a number')
        need(origin is not None, f'{name}: dates need time.start as a date')
        return (d - origin).days
    return num(v, name, -1e6, 1e6)


def timeline_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'tracks', 'milestones', 'today', 'today_label', 'durations', 'legend', 'status_labels'), 'timeline spec')
    sl = only(spec.get('status_labels') or {}, ('done', 'active', 'planned', 'late', 'risk'), 'status_labels')
    tm = only(spec.get('time'), ('start', 'end', 'unit'), 'time')
    clock = None
    if isinstance(tm.get('start'), str) and CLOCK.match(tm['start']):
        m = CLOCK.match(tm['start']); clock = int(m[1]) * 60 + int(m[2])
    origin = dt.date.fromisoformat(tm['start']) if isinstance(tm.get('start'), str) and clock is None else None
    day = lambda v, n: as_day(v, n, origin, clock)
    t0 = clock if clock is not None else (as_day(tm.get('start'), 'time.start', origin) if origin is None else 0)
    t1 = day(tm.get('end'), 'time.end')
    need(t1 > t0, 'time.end after time.start')
    tracks = spec.get('tracks'); need(isinstance(tracks, list) and 1 <= len(tracks) <= 10, 'tracks: 1-10')
    out = []
    for i, tr in enumerate(tracks):
        only(tr, ('label', 'start', 'end', 'status', 'note'), f'tracks[{i}]')
        a, b = day(tr.get('start'), f'tracks[{i}].start'), day(tr.get('end'), f'tracks[{i}].end')
        need(t0 <= a < b <= t1, f'tracks[{i}]: start < end, inside the time range')
        st = tr.get('status', 'planned'); need(st in ('done', 'active', 'planned', 'late', 'risk'), f'tracks[{i}].status: done|active|planned|late|risk')
        out.append(dict(label=text(tr.get('label'), f'tracks[{i}].label', 1, 16), a=a, b=b, status=st, note=text(tr['note'], 'note', 1, 16) if tr.get('note') else ''))
    ms = []
    for i, m in enumerate(spec.get('milestones') or []):
        only(m, ('at', 'label'), f'milestones[{i}]')
        ms.append([day(m.get('at'), f'milestones[{i}].at'), text(m.get('label'), 'milestone label', 1, 14)])
    today = day(spec['today'], 'today') if spec.get('today') is not None else None
    ticks = []
    if clock is not None:
        span = t1 - t0; step = next(x for x in (5, 10, 15, 30, 60, 120, 240) if span / x <= 7)
        hm = lambda x: f'{int(x) // 60 % 24:02d}:{int(x) % 60:02d}'
        ticks = [[x, hm(x)] for x in range(int(math.ceil(t0 / step) * step), int(t1) + 1, step)]
        label_day = hm
        dur = lambda d: ' '.join(x for x in (f'{int(d) // 60}시간' if d >= 60 else '', f'{int(d) % 60}분' if d % 60 or d < 60 else '') if x)
    elif origin is not None:
        d = dt.date(origin.year, origin.month, 1)
        while (d - origin).days <= t1:
            if (d - origin).days >= t0:
                ticks.append([(d - origin).days, f'{d.month}월'])
            d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        label_day = lambda x: f'{(origin + dt.timedelta(days=round(x))).month}/{(origin + dt.timedelta(days=round(x))).day}'
        dur = lambda d: f'{d:g}일'
    else:
        unit = text(tm.get('unit', '주'), 'time.unit', 1, 4)
        step = max(1, round((t1 - t0) / 6))
        ticks = [[x, f'{x:g}{unit}'] for x in range(int(t0), int(t1) + 1, step)]
        label_day = lambda x: f'{x:g}{unit}'
        dur = lambda d: f'{d:g}{unit}'
    if spec.get('durations'):   # e.g. incident reviews: how long detection, response and recovery took
        for x in out:
            x['note'] = x['note'] or dur(x['b'] - x['a'])
    tl = text(spec.get('today_label', '오늘'), 'today_label', 1, 6)
    data = dict(scene='timeline', time=dict(unit='', end=1.0, start=t0, stop=t1), tracks=out, milestones=[[a, l, label_day(a)] for a, l in ms],
                today=[today, tl + ' ' + label_day(today)] if today is not None else None, ticks=ticks, legend=spec.get('legend', True),
                status_labels={k: text(v, f'status_labels.{k}', 1, 8) for k, v in sl.items()},
                captions=[[1.0, '', claim]], rate=[[0, 1]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    head = ['항목', '시작', '끝', '상태']
    names = dict(done='완료', active='진행', planned='예정', late='지연', risk='위험')
    rows = [[x['label'], label_day(x['a']), label_day(x['b']), names[x['status']]] for x in out]
    checks = dict(end=1.0, samples=[1.0] * 6, annotations=[], expect=None, resize_at=0.5)
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}).', table=(head, rows),
                checks=checks, live=False, numeric=dict(tracks=out), title=title)


# ---------------------------------------------------------------- diagram
NODE_TYPES = {'system': '', 'person': '', 'ai': 'AI·에이전트', 'data': '데이터', 'external': '외부 서비스'}
NODE_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,23}$')


def diagram_data(spec):
    """Structure and request paths: components in layers, connections, optional numbered steps.
    Layout rules are enforced here so the scene never has to route a line through a box:
    edges join adjacent layers, neighbours in one layer, or (longer jumps) the first or last
    components of their layers through a lane outside every box."""
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'layers', 'edges', 'groups', 'steps', 'highlight', 'dashed_means'), 'diagram spec')
    layers = spec.get('layers')
    need(isinstance(layers, list) and 1 <= len(layers) <= 5, 'layers: 1-5 layers (left to right on wide screens, top to bottom on phones)')
    out, where = [], {}
    for i, ly in enumerate(layers):
        only(ly, ('label', 'nodes'), f'layers[{i}]')
        nodes = ly.get('nodes')
        need(isinstance(nodes, list) and 1 <= len(nodes) <= 4, f'layers[{i}].nodes: 1-4 components per layer')
        row = []
        for j, nd in enumerate(nodes):
            nm = f'layers[{i}].nodes[{j}]'
            only(nd, ('id', 'name', 'sub', 'type'), nm)
            nid = nd.get('id'); need(isinstance(nid, str) and NODE_ID.match(nid), f'{nm}.id: letters, digits, _ or - (max 24), starting with a letter')
            need(nid not in where, f'{nm}.id: "{nid}" used twice')
            tp = nd.get('type', 'system'); need(tp in NODE_TYPES, f'{nm}.type: one of {list(NODE_TYPES)}')
            where[nid] = (i, j)
            row.append(dict(id=nid, name=text(nd.get('name'), f'{nm}.name', 1, 14), sub=text(nd['sub'], f'{nm}.sub', 1, 18) if nd.get('sub') else '', type=tp))
        out.append(dict(label=text(ly['label'], f'layers[{i}].label', 1, 14) if ly.get('label') else '', nodes=row))
    need(sum(len(x['nodes']) for x in out) <= 14, 'diagram: at most 14 components; split it into two diagrams')
    edges, seen = [], set()
    for k, e in enumerate(spec.get('edges') or []):
        nm = f'edges[{k}]'
        only(e, ('from', 'to', 'label', 'style'), nm)
        a, b = e.get('from'), e.get('to')
        need(a in where and b in where, f'{nm}: unknown component; ids are {", ".join(where)}')
        need(a != b and (a, b) not in seen, f'{nm}: {a} -> {b} is a self-loop or a duplicate')
        seen.add((a, b))
        (la, ia), (lb, ib) = where[a], where[b]
        if la == lb:
            need(abs(ia - ib) == 1, f'{nm}: within one layer only neighbours can connect ({a}, {b}); reorder the layer')
            route = 'side'
        elif abs(la - lb) == 1:
            route = 'next'
        else:
            first = ia == 0 and ib == 0
            last = ia == len(out[la]['nodes']) - 1 and ib == len(out[lb]['nodes']) - 1
            need(first or last, f'{nm}: {a} -> {b} skips a layer; put both first (or both last) in their layers so the line can run outside the boxes')
            route = 'over' if first else 'under'
        style = e.get('style', 'solid'); need(style in ('solid', 'dashed'), f'{nm}.style: solid or dashed')
        edges.append(dict(a=a, b=b, label=text(e['label'], f'{nm}.label', 1, 12) if e.get('label') else '', dashed=style == 'dashed', route=route))
    need(len(edges) <= 24, 'edges: at most 24 connections')
    groups = []
    for k, gp in enumerate(spec.get('groups') or []):
        only(gp, ('label', 'layers'), f'groups[{k}]')
        rg = gp.get('layers')
        need(isinstance(rg, list) and len(rg) == 2 and all(isinstance(x, int) for x in rg) and 0 <= rg[0] <= rg[1] < len(out),
             f'groups[{k}].layers: [first, last] layer indexes (0-based)')
        need(all(rg[1] < g['a'] or rg[0] > g['b'] for g in groups), f'groups[{k}]: groups may not overlap')
        groups.append(dict(label=text(gp.get('label'), f'groups[{k}].label', 1, 16), a=rg[0], b=rg[1]))
    need(len(groups) <= 3, 'groups: at most 3')
    hl = spec.get('highlight') or []
    need(isinstance(hl, list) and all(x in where for x in hl), 'highlight: list of component ids')
    index = {(e['a'], e['b']): i for i, e in enumerate(edges)}
    steps = []
    for k, st in enumerate(spec.get('steps') or []):
        nm = f'steps[{k}]'
        only(st, ('path', 'paths', 'text'), nm)
        need(('path' in st) != ('paths' in st), f'{nm}: give "path" (one route) or "paths" (routes that happen at the same time)')
        paths = [st['path']] if 'path' in st else st['paths']
        need(isinstance(paths, list) and 1 <= len(paths) <= 3, f'{nm}.paths: 1-3 routes')
        routes, nodes = [], []
        for path in paths:
            need(isinstance(path, list) and len(path) >= 2 and all(x in where for x in path), f'{nm}.path: two or more component ids')
            for a, b in zip(path, path[1:]):
                need((a, b) in index, f'{nm}.path: no connection {a} -> {b}; add it to edges (direction matters)')
            routes.append([index[(a, b)] for a, b in zip(path, path[1:])])
            nodes += [x for x in path if x not in nodes]
        steps.append(dict(edges=[i for r in routes for i in r], paths=routes, nodes=nodes,
                          text=text(fill(text(st.get('text'), f'{nm}.text', 2, 80), {}, f'{nm}.text'), f'{nm}.text', 2, 40)))
    need(len(steps) <= 6, 'steps: at most 6; a longer story needs two diagrams or prose')
    for i, x in enumerate(steps):
        x['mark'] = CIRCLED[i]
    live = bool(steps) and motion != 'none'
    end = float(max(1, len(steps)))
    captions = [[0.0 if live else end, '', claim]]
    rate = [[0, 0.25]] if live else [[0, 1]]   # one step ~3.2 s at the default 1.25x
    dm = text(spec.get('dashed_means', '비동기·선택'), 'dashed_means', 1, 14)
    data = dict(scene='diagram', time=dict(unit='', end=end), layers=out, edges=edges, groups=groups, steps=steps, highlight=hl, dashed_means=dm,
                types={k: v for k, v in NODE_TYPES.items() if v and any(n['type'] == k for x in out for n in x['nodes'])},
                captions=captions, rate=rate, labels=dict(data_kind=DIAGRAM_KINDS[data_kind]))
    n = len(steps)

    def expect(T):
        return dict(state={'step': n if T >= end - 1e-9 else min(n - 1, math.floor(T + 1e-9))}, stats=[])
    samples = [round(i + 0.4, 4) for i in range(n)][:5] + [end]
    while len(samples) < 6:
        samples.append(end)
    checks = dict(end=end, samples=samples, annotations=[], expect=expect if live else None, resize_at=round(end / 2, 4))
    name = {x['id']: x['name'] for ly in out for x in ly['nodes']}
    head = ['구분', '항목', '설명']
    rows = [[f'구성 요소 · {ly["label"] or i + 1}', x['name'], x['sub'] or NODE_TYPES[x['type']] or '-'] for i, ly in enumerate(out) for x in ly['nodes']]
    rows += [['연결', f'{name[e["a"]]} → {name[e["b"]]}', (e['label'] or '-') + (' (점선)' if e['dashed'] else '')] for e in edges]
    route = lambda r: ' → '.join([name[edges[r[0]]['a']]] + [name[edges[i]['b']] for i in r])
    rows += [[f'단계 {x["mark"]}', ' · '.join(route(r) for r in x['paths']), x['text']] for x in steps]
    return dict(data=data, aria=f'{title}. {claim}', notes=f'근거: {source} ({DIAGRAM_KINDS[data_kind]}).', table=(head, rows),
                checks=checks, live=live, numeric=dict(steps=n), title=title)


# ---------------------------------------------------------------- distribution
MARKERS = {'mean': ('평균', 'blue'), 'p50': ('P50', 'green'), 'p95': ('P95', 'amber'), 'p99': ('P99', 'red')}


def distribution_data(spec):
    """One dot per observation, stacked by value; mean and percentiles appear one at a time.
    The point is the shape: two samples with the same average can have very different tails."""
    from monitoring_cases import stats
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'unit', 'max', 'groups', 'markers', 'tail', 'captions'), 'distribution spec')
    unit = text(spec.get('unit', ''), 'unit', 0, 6) if spec.get('unit') else ''
    groups = []
    for gi, g in enumerate(spec.get('groups') or []):
        only(g, ('label', 'values', 'counts'), f'groups[{gi}]')
        vs, cs = g.get('values'), g.get('counts')
        need(isinstance(vs, list) and isinstance(cs, list) and 1 <= len(vs) == len(cs) <= 40, f'groups[{gi}]: values and counts of equal length (1-40)')
        vs = [num(v, 'value', 0) for v in vs]; cs = [int(num(c, 'count', 0, 200)) for c in cs]
        need(all(a < b for a, b in zip(vs, vs[1:])), f'groups[{gi}].values: increasing'); need(sum(cs) <= 120, f'groups[{gi}]: at most 120 observations')
        st = stats(vs, cs)
        groups.append(dict(label=text(g.get('label'), f'groups[{gi}].label', 1, 16), values=vs, counts=cs, stats={k: st[k] for k in ('n', 'mean', 'p50', 'p95', 'p99')}))
    need(1 <= len(groups) <= 3, 'groups: 1-3 samples')
    vmax = num(spec.get('max', nice_max(max(v for g in groups for v in g['values']) * 1.1)), 'max', 1e-9)
    marks = spec.get('markers', ['mean', 'p50', 'p95', 'p99'])
    need(isinstance(marks, list) and all(m in MARKERS for m in marks), f'markers: subset of {list(MARKERS)}')
    n_dots = max(g['stats']['n'] for g in groups)
    t_dots = 3.0; events = {'start': 0.0}; t = t_dots + .5
    for m in marks:
        events[m] = t; t += 1.2
    tail = None
    if spec.get('tail'):
        tl = only(spec['tail'], ('from', 'label'), 'tail'); a = num(tl.get('from'), 'tail.from', 0, vmax)
        share = {g['label']: sum(c for v, c in zip(g['values'], g['counts']) if v >= a) / g['stats']['n'] * 100 for g in groups}
        events['tail'] = t; t += 1.2
        lab = {g['label']: fill(text(tl.get('label', '긴 꼬리 ({share}%)'), 'tail.label', 1, 40), {'share': f'{share[g["label"]]:.0f}'}, 'tail.label') for g in groups}
        tail = dict(at=a, labels=lab, shares=share)
    end = t + .8; events['end'] = end
    values = {'end': fmt(end)}
    for gi, g in enumerate(groups):
        for k, v in g['stats'].items():
            values[f'{k}' + (f'@{gi}' if gi else '')] = fmt(v)
    captions = captions_from(spec, events, values, end)
    live = motion != 'none' and len(captions) >= 2
    if not captions:
        captions = [[end, '', claim]]
    rate = paced_rate(captions, end, [[0, .9]]) if live else [[0, 1]]
    data = dict(scene='distribution', time=dict(unit='', end=end, dots=t_dots), unit=unit, max=vmax, groups=groups,
                markers=[[m, MARKERS[m][0], MARKERS[m][1], events[m]] for m in marks], tail=tail and dict(at=tail['at'], labels=tail['labels'], shares=tail['shares'], t=events['tail']),
                captions=captions, rate=rate, labels=dict(data_kind=DATA_KINDS[data_kind]))
    def expect(T):
        return dict(state={'shown': [min(g['stats']['n'], math.floor(g['stats']['n'] * min(1, T / t_dots) + 1e-9)) for g in groups]}, stats=[])
    ann = [[f'{MARKERS[m][0]} {fmt(groups[0]["stats"][m])}{unit}', events[m]] for m in marks]
    samples = [1.5, events[marks[0]] + .3, events[marks[-1]] + .3, end] if marks else [1.5, end]
    while len(samples) < 6:
        samples.append(end)
    checks = dict(end=end, samples=samples, annotations=ann, expect=expect if live else None, resize_at=round(end / 2, 4))
    head = ['표본'] + [MARKERS[m][0] for m in ['mean', 'p50', 'p95', 'p99']] + ['요청 수']
    rows = [[g['label']] + [fmt(g['stats'][m]) + unit for m in ['mean', 'p50', 'p95', 'p99']] + [g['stats']['n']] for g in groups]
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}). 점 1개 = 요청 1건.', table=(head, rows),
                checks=checks, live=live, numeric={g['label']: g['stats'] for g in groups}, title=title)


BUILDERS = dict(flow=flow_data, trend=trend_data, bars=bars_data, share=share_data, timeline=timeline_data, diagram=diagram_data, distribution=distribution_data)


def build(spec):
    need(isinstance(spec, dict), 'spec: JSON object required')
    kind = spec.get('kind'); need(kind in BUILDERS, f'kind must be one of {KINDS}')
    return BUILDERS[kind](spec)
