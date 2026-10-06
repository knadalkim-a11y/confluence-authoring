"""share: how a whole splits and how the split changed (instead of a pie)."""
from __future__ import annotations
from kinds.common import DATA_KINDS, common, decimals_of, fmt, need, num, only, text


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
