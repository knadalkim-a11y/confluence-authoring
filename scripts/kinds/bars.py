"""bars: comparison and before/after; "mode": "funnel" for drop-off between steps."""
from __future__ import annotations
from model import nice_max
from kinds.common import DATA_KINDS, common, decimals_of, fmt, need, num, only, text


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
