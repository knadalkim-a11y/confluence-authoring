"""trend: metrics over time, around events and against targets."""
from __future__ import annotations
import re
from model import interp, nice_max, paced_rate
from kinds.common import COLORS, DATA_KINDS, captions_from, common, decimals_of, fill, fmt, need, num, only, r1, resolve_at, text


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
    # a reveal at the very end gets a short settle after the axis ends, so it enters instead of snapping
    reveals = [e[0] for e in ev_marks] + [x[0] for x in notes_on] + [b[1] for b in bands] + [e[0] for g in groups for e in g['events']] \
        + [x[0] for g in groups for x in g['pill'] + g['note']] + [ln[0] for ln in ((log or {}).get('lines') or [])]
    r_end = [r for t0, r in rate if end >= t0 - 1e-9][-1]
    settle = round(0.5 * r_end, 4) if live and any(t > end - 0.5 * r_end for t in reveals) else 0.0
    fin = end + settle
    data = dict(scene='trend', time=dict(unit=tu, end=end, settle=settle), groups=groups, thresholds=thresholds, events=ev_marks, ticks=ticks,
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
    samples = [x if x < end - 1e-9 else fin for x in samples]
    checks = dict(end=fin, samples=samples[:6] if fin in samples[:6] else samples[:5] + [fin], annotations=ann, expect=expect, resize_at=round(end / 2, 4), choreo=True)
    notes = f'출처: {source} ({DATA_KINDS[data_kind]}). 가로축은 {tu} 단위 시간입니다.'
    head = ['시각'] + [f'{p["label"]} · {s["name"]}' for g in groups for p in g['panels'] for s in p['series']]
    grid = sorted({x for g in groups for p in g['panels'] for s in p['series'] for x in s['t']})
    step = max(1, len(grid) // 20)
    rows = [[fmt(T, 2)] + [fmt(interp(s['t'], s['v'], T), p['decimals']) for g in groups for p in g['panels'] for s in p['series']] for T in grid[::step]]
    return dict(data=data, aria=f'{title}. {claim}', notes=notes, table=(head, rows), checks=checks, live=live, numeric=dict(values=values), title=title)
