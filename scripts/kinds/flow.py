"""flow: backlog, queue and capacity; a fluid model per lane, tokens and model events bind the captions."""
from __future__ import annotations
import choreo
from model import first_reach, fluid_tokens, grp, interp, nice_max, paced_rate, token_speed
from kinds.common import DATA_KINDS, TONES, captions_from, common, fill, fmt, need, num, only, r1, resolve_at, text


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
    cues = []   # the bottleneck heats up when a queue forms and cools when it drains (choreo.py)
    for i, l in enumerate(lanes):
        ts_, vs_ = choreo.switches(l['S']['t'], [q > 1e-6 for q in l['S']['q']], rate)
        cues += choreo.levels(f'q{i}', 'act', vs_, ts_, rate)
    cues = choreo.validate(cues, end)
    data = dict(scene='flow', time=dict(unit=tu, end=end), cues=cues, inflow=sched, unit=unit, speed=token_speed(peak, unit, rate), labels=labels,
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
    checks = dict(end=end, samples=samples, annotations=[[a, round(b, 6)] for a, b in ann if 0 < b < end], expect=expect, resize_at=round(end / 2, 4), choreo=True)
    table = (head, rows)
    numeric = dict(lanes=[dict(name=l['name'], queue_end=l['S']['q'][-1], served_end=l['S']['srv'][-1], rejected_end=l['S']['rej'][-1]) for l in lanes],
                   events={k: v for k, v in events.items() if v is not None}, unit=unit)
    return dict(data=data, aria=aria, notes=notes, table=table, checks=checks, live=live, numeric=numeric, title=title)
