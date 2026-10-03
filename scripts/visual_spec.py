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

KINDS = ('flow', 'trend', 'bars', 'timeline')
DATA_KINDS = {'measured': '측정값', 'estimate': '추정값', 'example': '예시 데이터'}
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
    legend = [f'점 1개 = {grp(unit)}{count_u}']
    if any(l['limit'] for l in lanes):
        legend.append(f'상한 칸 1개 = 1{count_u}')
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
        st = {'queue': [round(max(0, interp(t, l['S']['q'], T)), 1) for l in lanes], 'rejected': [round(max(0, interp(t, l['S']['rej'], T)), 1) for l in lanes]}
        stats = []
        if len(lanes) == 1:
            l = lanes[0]; cap = l['stages'][l['b']]['capacity']; i = next((k for k in range(1, len(t)) if t[k] > T + 1e-9), len(t) - 1)
            served = (l['S']['srv'][i] - l['S']['srv'][i - 1]) / (t[i] - t[i - 1])
            stats = [grp(schedule_rate(sched, T)), grp(served), f'{max(0, interp(t, l["S"]["q"], T)) / cap:.1f}']   # same formatting as the scene
        return dict(state=st, stats=stats)
    ann = [[c[2], c[1]] for c in callouts]
    if len(lanes) == 1 and max(lanes[0]['S']['q']) > 1e-6:   # history strip peak label appears at the peak
        qq = lanes[0]['S']['q']; ann.append([f'최대 {grp(max(qq))}{count_u}', lanes[0]['S']['t'][qq.index(max(qq))]])
    for li, l in enumerate(lanes):
        if len(l['stages']) > 1 and events.get('queue' if li == 0 else f'queue@{li}') is not None:
            ann.append([labels['limit_pill'], events['queue' if li == 0 else f'queue@{li}']])   # pill appears as soon as the queue does
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
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'groups', 'panels', 'events', 'thresholds', 'captions'), 'trend spec')
    tm = only(spec.get('time'), ('unit', 'end', 'ticks', 'start'), 'time')
    tu = text(tm.get('unit'), 'time.unit', 1, 4); end = num(tm.get('end'), 'time.end', 1e-6, 1e7); start = num(tm.get('start', 0), 'time.start', -1e7, end)
    need(start == 0, 'time.start must be 0 (shift your time values)')
    groups_raw = spec.get('groups') or [dict(panels=spec.get('panels'))]
    need(isinstance(groups_raw, list) and 1 <= len(groups_raw) <= 3, 'groups: 1-3')
    events, values, groups = {'start': 0.0, 'end': end}, {'end': fmt(end), 'time_unit': tu}, []
    for e in spec.get('events') or []:
        only(e, ('at', 'label', 'name'), 'events[]')
        nm = e.get('name') or e.get('label'); events[nm] = num(e.get('at'), f'event {nm}', 0, end)
    for gi, g in enumerate(groups_raw):
        only(g, ('name', 'pill', 'note', 'panels'), f'groups[{gi}]')
        panels = []
        need(isinstance(g.get('panels'), list) and 1 <= len(g['panels']) <= 4, f'groups[{gi}].panels: 1-4 panels')
        for pi, p in enumerate(g['panels']):
            only(p, ('label', 'unit', 'max', 'ticks', 'series', 'decimals'), f'groups[{gi}].panels[{pi}]')
            series = []
            need(isinstance(p.get('series'), list) and 1 <= len(p['series']) <= 3, f'panel {pi}: 1-3 series')
            for si, s in enumerate(p['series']):
                only(s, ('name', 'color', 'points'), f'panel {pi} series {si}')
                pts = s.get('points'); need(isinstance(pts, list) and 2 <= len(pts) <= 2000, f'series {si}: 2-2000 [t, v] points')
                pts = [[num(a, 'time', 0, end), num(b, 'value')] for a, b in pts]
                need(all(a[0] < b[0] for a, b in zip(pts, pts[1:])), f'series {si}: times increasing')
                need(pts[0][0] == 0 and abs(pts[-1][0] - end) < 1e-9, f'series {si}: points must cover 0..{end:g}')
                color = s.get('color', COLORS[si]); need(color in COLORS, f'series {si}: color in {COLORS}')
                series.append(dict(name=text(s.get('name'), 'series.name', 1, 20), color=color, t=[x[0] for x in pts], v=[x[1] for x in pts]))
                key = re.sub(r'\W+', '_', series[-1]['name']).strip('_') or f's{si}'
                values[f'{key}_end' + (f'@{gi}' if gi else '')] = fmt(pts[-1][1], p.get('decimals'))
                values[f'{key}_max' + (f'@{gi}' if gi else '')] = fmt(max(x[1] for x in pts), p.get('decimals'))
            vmax = p.get('max', nice_max(max(max(s['v']) for s in series)))
            unit = text(p.get('unit', ''), 'unit', 0, 6) if p.get('unit') else ''
            ticks = p.get('ticks') or [vmax, vmax / 2, 0]
            dec = p.get('decimals') if p.get('decimals') is not None else decimals_of([v for s in series for v in s['v']], 1)
            panels.append(dict(label=text(p.get('label'), 'panel.label', 1, 24), unit=unit, max=num(vmax, 'max', 1e-9), series=series,
                               ticks=[num(x, 'tick') for x in ticks], decimals=dec))
        def timed(lst, name, ln):
            out = []
            for i, x in enumerate(lst or []):
                need(isinstance(x, list) and len(x) == 3, f'{name}[{i}]: [at, text, tone]')
                need(x[2] in ('ok', 'warn', 'hot', 'info'), f'{name}[{i}] tone: ok|warn|hot|info')
                out.append([resolve_at(x[0], events, name), fill(text(x[1], name, 1, ln), values, name), x[2]])
            return sorted(out, key=lambda x: x[0])
        groups.append(dict(name=g.get('name', ''), pill=timed(g.get('pill'), f'groups[{gi}].pill', 24), note=timed(g.get('note'), f'groups[{gi}].note', 30), panels=panels))
    thresholds = []
    for i, th in enumerate(spec.get('thresholds') or []):
        only(th, ('panel', 'value', 'label'), f'thresholds[{i}]')
        thresholds.append([text(th.get('panel'), 'thresholds.panel', 1, 24), num(th.get('value'), 'thresholds.value'), text(th.get('label'), 'thresholds.label', 1, 20)])
    ev_marks = [[events[e.get('name') or e.get('label')], text(e.get('label'), 'event label', 1, 16)] for e in spec.get('events') or []]
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
                captions=captions, rate=rate, labels=dict(data_kind=DATA_KINDS[data_kind]))
    def expect(T):
        return dict(state={'values': [[[round(interp(s['t'], s['v'], T), 1) for s in p['series']] for p in g['panels']] for g in groups]}, stats=[])
    ann = [[x[1], x[0]] for g in groups for x in g['pill'] + g['note'] if 0 < x[0] < end] + [[lb, at] for at, lb in ev_marks if 0 < at < end]
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
                'decimals', 'max', 'pair_labels', 'flat_pct'), 'bars spec')
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
                better=better, pair_labels=pl, decimals=dec, flat_pct=flat, captions=captions, rate=[[0, 0.35]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    head = ['항목'] + ([pl[0], pl[1], '변화'] if paired else ['값'])
    rows = [[x['label'], fmt(x['before'], dec), fmt(x['after'], dec), (fmt(100 * (x['after'] - x['before']) / x['before'], 1) + '%') if x['before'] else '-']
            if paired else [x['label'], fmt(x['value'], dec)] for x in out]
    checks = dict(end=1.0, samples=[0.3, 0.6, 1.0, 1.0, 1.0, 1.0], annotations=[], expect=None, resize_at=0.5)
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}). 단위: {unit or "-"}.',
                table=(head, rows), checks=checks, live=live, numeric=dict(items=out), title=title)


# ---------------------------------------------------------------- timeline
def as_day(v, name, origin):
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
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'tracks', 'milestones', 'today'), 'timeline spec')
    tm = only(spec.get('time'), ('start', 'end', 'unit'), 'time')
    origin = dt.date.fromisoformat(tm['start']) if isinstance(tm.get('start'), str) else None
    t0 = as_day(tm.get('start'), 'time.start', origin) if origin is None else 0
    t1 = as_day(tm.get('end'), 'time.end', origin)
    need(t1 > t0, 'time.end after time.start')
    tracks = spec.get('tracks'); need(isinstance(tracks, list) and 1 <= len(tracks) <= 10, 'tracks: 1-10')
    out = []
    for i, tr in enumerate(tracks):
        only(tr, ('label', 'start', 'end', 'status', 'note'), f'tracks[{i}]')
        a, b = as_day(tr.get('start'), f'tracks[{i}].start', origin), as_day(tr.get('end'), f'tracks[{i}].end', origin)
        need(t0 <= a < b <= t1, f'tracks[{i}]: start < end, inside the time range')
        st = tr.get('status', 'planned'); need(st in ('done', 'active', 'planned', 'late', 'risk'), f'tracks[{i}].status: done|active|planned|late|risk')
        out.append(dict(label=text(tr.get('label'), f'tracks[{i}].label', 1, 16), a=a, b=b, status=st, note=text(tr['note'], 'note', 1, 16) if tr.get('note') else ''))
    ms = []
    for i, m in enumerate(spec.get('milestones') or []):
        only(m, ('at', 'label'), f'milestones[{i}]')
        ms.append([as_day(m.get('at'), f'milestones[{i}].at', origin), text(m.get('label'), 'milestone label', 1, 14)])
    today = as_day(spec['today'], 'today', origin) if spec.get('today') is not None else None
    ticks = []
    if origin is not None:
        d = dt.date(origin.year, origin.month, 1)
        while (d - origin).days <= t1:
            if (d - origin).days >= t0:
                ticks.append([(d - origin).days, f'{d.month}월'])
            d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        label_day = lambda x: f'{(origin + dt.timedelta(days=round(x))).month}/{(origin + dt.timedelta(days=round(x))).day}'
    else:
        unit = text(tm.get('unit', '주'), 'time.unit', 1, 4)
        step = max(1, round((t1 - t0) / 6))
        ticks = [[x, f'{x:g}{unit}'] for x in range(int(t0), int(t1) + 1, step)]
        label_day = lambda x: f'{x:g}{unit}'
    data = dict(scene='timeline', time=dict(unit='', end=1.0, start=t0, stop=t1), tracks=out, milestones=[[a, l, label_day(a)] for a, l in ms],
                today=[today, '오늘 ' + label_day(today)] if today is not None else None, ticks=ticks,
                captions=[[1.0, '', claim]], rate=[[0, 1]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    head = ['항목', '시작', '끝', '상태']
    names = dict(done='완료', active='진행', planned='예정', late='지연', risk='위험')
    rows = [[x['label'], label_day(x['a']), label_day(x['b']), names[x['status']]] for x in out]
    checks = dict(end=1.0, samples=[1.0] * 6, annotations=[], expect=None, resize_at=0.5)
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}).', table=(head, rows),
                checks=checks, live=False, numeric=dict(tracks=out), title=title)


BUILDERS = dict(flow=flow_data, trend=trend_data, bars=bars_data, timeline=timeline_data)


def build(spec):
    need(isinstance(spec, dict), 'spec: JSON object required')
    kind = spec.get('kind'); need(kind in BUILDERS, f'kind must be one of {KINDS}')
    return BUILDERS[kind](spec)
