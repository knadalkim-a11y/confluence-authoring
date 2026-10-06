"""distribution: how values spread; mean versus percentiles."""
from __future__ import annotations
import math
from model import nice_max, paced_rate
from kinds.common import DATA_KINDS, captions_from, common, fill, fmt, need, num, only, text


MARKERS = {'mean': ('평균', 'blue'), 'p50': ('P50', 'green'), 'p95': ('P95', 'amber'), 'p99': ('P99', 'red')}


def distribution_data(spec):
    """One dot per observation, stacked by value; mean and percentiles appear one at a time.
    The point is the shape: two samples with the same average can have very different tails."""
    from model import stats
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
