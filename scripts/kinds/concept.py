"""concept: compare / stack / sequence presets drawn by the compose engine."""
from __future__ import annotations
from kinds.common import CIRCLED, common, need, only, text
from kinds.diagram import ROLE_TONES
from kinds.compose import compose_build


CONCEPT_FORMS = ('compare', 'stack', 'sequence')


def concept_data(spec):
    """Concept figures (docs/design/motion-concept-architecture.md, section 10), now presets of the compose engine:
    compare  - 2-3 columns side by side (without/with, before/after, two viewpoints) -> split of labelled columns;
    stack    - bands stacked top to bottom (a context window, layers) with an optional side bracket -> stack;
    sequence - 2-4 actors with lifelines and numbered messages (a call, a hand-off) -> lifelines.
    The spec stays as before; only the drawing moved to the shared engine."""
    kind, title, claim, source, data_kind, motion = common(spec)
    form = spec.get('form'); need(form in CONCEPT_FORMS, f'form: one of {CONCEPT_FORMS}')
    base = ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'form')
    tone = lambda v, nm, d: (v if v is not None else d) if (v is None or v in ROLE_TONES) else need(False, f'{nm}: one of {list(ROLE_TONES)}')
    rows = []
    if form == 'compare':
        only(spec, base + ('columns', 'arrow'), 'concept spec (compare)')
        cols = spec.get('columns'); need(isinstance(cols, list) and 2 <= len(cols) <= 3, 'columns: 2-3 (e.g. 경계 없음 / 경계 있음)')
        parts = []
        for i, c in enumerate(cols):
            nm = f'columns[{i}]'; only(c, ('label', 'tone', 'items', 'note'), nm)
            items = c.get('items'); need(isinstance(items, list) and 1 <= len(items) <= 6, f'{nm}.items: 1-6')
            ct = tone(c.get('tone'), f'{nm}.tone', ['gray', 'blue', 'green'][i])
            its = []
            for j, it in enumerate(items):
                only(it, ('name', 'sub', 'tone'), f'{nm}.items[{j}]')
                text(it.get('name'), f'{nm}.items[{j}].name', 1, 16)
                its.append(dict(id=f'c{i}_{j}', name=it['name'], tone=tone(it.get('tone'), f'{nm}.items[{j}].tone', ct), **({'sub': text(it['sub'], f'{nm}.items[{j}].sub', 1, 22)} if it.get('sub') else {})))
                rows.append([c.get('label'), it['name'], it.get('sub') or ''])
            parts.append(dict(layout='column', id=f'col{i}', label=text(c.get('label'), f'{nm}.label', 1, 14), tone=ct, items=its,
                              **({'note': text(c['note'], f'{nm}.note', 1, 40)} if c.get('note') else {})))
        root = dict(layout='split', items=parts, **({'arrow': text(spec['arrow'], 'arrow', 1, 10)} if spec.get('arrow') else {}))
        root['id'] = 'split'
    elif form == 'stack':
        only(spec, base + ('layers', 'bracket', 'free'), 'concept spec (stack)')
        lys = spec.get('layers'); need(isinstance(lys, list) and 2 <= len(lys) <= 7, 'layers: 2-7, listed top to bottom')
        bands = []
        for i, l in enumerate(lys):
            nm = f'layers[{i}]'; only(l, ('name', 'sub', 'tone', 'size'), nm)
            text(l.get('name'), f'{nm}.name', 1, 18)
            bands.append(dict(id=f'l{i}', name=l['name'], tone=tone(l.get('tone'), f'{nm}.tone', 'blue'), size=l.get('size', 1),
                              **({'sub': text(l['sub'], f'{nm}.sub', 1, 28)} if l.get('sub') else {})))
            rows.append([f'{i + 1}', l['name'], l.get('sub') or ''])
        root = dict(layout='stack', id='stack', items=bands, **{k: spec[k] for k in ('bracket', 'free') if spec.get(k)})
    else:
        only(spec, base + ('actors', 'messages'), 'concept spec (sequence)')
        acts = spec.get('actors'); need(isinstance(acts, list) and 2 <= len(acts) <= 4, 'actors: 2-4')
        actors = []
        for i, a in enumerate(acts):
            nm = f'actors[{i}]'; only(a, ('id', 'name', 'tone'), nm)
            text(a.get('name'), f'{nm}.name', 1, 10)
            actors.append(dict(id=a.get('id'), name=a['name'], tone=tone(a.get('tone'), f'{nm}.tone', ['gray', 'blue', 'purple', 'green'][i])))
        msgs = spec.get('messages'); need(isinstance(msgs, list) and 1 <= len(msgs) <= 8, 'messages: 1-8, in order')
        nmap = {a['id']: a['name'] for a in actors}
        for k, m in enumerate(msgs):
            rows.append([CIRCLED[k], f'{nmap.get(m.get("from"), "?")} → {nmap.get(m.get("to"), "?")}', m.get('text', '')])
        root = dict(layout='lifelines', id='life', items=actors, messages=msgs)
    head = {'compare': ['구분', '항목', '설명'], 'stack': ['순서(위→아래)', '층', '설명'], 'sequence': ['순서', '방향', '메시지']}[form]
    out = compose_build(spec, root, [], None, head, rows)
    out['numeric'] = dict(form=form, units=len(rows))
    return out
