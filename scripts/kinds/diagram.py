"""diagram: architecture, components and connections; with steps the path a request takes. Its own tuned scene (visuals/live/scenes/diagram.js)."""
from __future__ import annotations
import choreo
import math
import re
from kinds.common import CIRCLED, DIAGRAM_KINDS, common, fill, need, only, text


ROLE_TONES = ('blue', 'green', 'amber', 'purple', 'red', 'gray')   # visuals/live/kit.js K.TONE
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
            only(nd, ('id', 'name', 'sub', 'type', 'tone'), nm)
            nid = nd.get('id'); need(isinstance(nid, str) and NODE_ID.match(nid), f'{nm}.id: letters, digits, _ or - (max 24), starting with a letter')
            need(nid not in where, f'{nm}.id: "{nid}" used twice')
            tp = nd.get('type', 'system'); need(tp in NODE_TYPES, f'{nm}.type: one of {list(NODE_TYPES)}')
            tone = nd.get('tone'); need(tone is None or tone in ROLE_TONES, f'{nm}.tone: one of {list(ROLE_TONES)}')
            where[nid] = (i, j)
            row.append(dict(id=nid, name=text(nd.get('name'), f'{nm}.name', 1, 14), sub=text(nd['sub'], f'{nm}.sub', 1, 18) if nd.get('sub') else '', type=tp, tone=tone or ''))
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
        only(gp, ('label', 'layers', 'tone'), f'groups[{k}]')
        gt = gp.get('tone'); need(gt is None or gt in ROLE_TONES, f'groups[{k}].tone: one of {list(ROLE_TONES)} (a boundary, e.g. 신뢰 영역)')
        rg = gp.get('layers')
        need(isinstance(rg, list) and len(rg) == 2 and all(isinstance(x, int) for x in rg) and 0 <= rg[0] <= rg[1] < len(out),
             f'groups[{k}].layers: [first, last] layer indexes (0-based)')
        need(all(rg[1] < g['a'] or rg[0] > g['b'] for g in groups), f'groups[{k}]: groups may not overlap')
        groups.append(dict(label=text(gp.get('label'), f'groups[{k}].label', 1, 16), a=rg[0], b=rg[1], tone=gt or ''))
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
    n = len(steps)
    # default choreography (choreo.py): step k starts at k; the old step falls back first, the new one
    # rises as that fall is 80% through; the last 0.5 s settles everything into the final (static) scene
    end = float(n) + 0.5 if n else 1.0
    rate = [[0, 0.25]] if live else [[0, 1]]   # one step ~3.2 s at the default 1.25x
    cues = []
    if n:
        times = list(range(n + 1))
        used = lambda i, k: any(i in steps[j]['edges'] for j in range(k))
        for i in range(len(edges)):
            seq = [2 if i in steps[k]['edges'] else 1 if used(i, k) else 0 for k in range(n)] + [1 if used(i, n) else 0]
            cues += choreo.levels(f'e{i}', 'level', seq, times, rate)
        for nid in {x for st in steps for x in st['nodes']}:
            seq = [1 if nid in steps[k]['nodes'] else 0 for k in range(n)] + [0]
            lv = choreo.levels(f'n:{nid}', 'act', seq, times, rate)
            cues += lv + [choreo.cue(f'n:{nid}', 'pop', c[2], 0.4, 0, 1, 'linear', rate) for c in lv if c[6] > c[5]]
        for l in range(n):
            cues += choreo.levels(f'l{l}', 'on', [2 if l == k else 1 if l < k else 0 for k in range(n)] + [1], times, rate)
        cues = choreo.validate(cues, end)
    captions = [[0.0 if live else end, '', claim]]
    dm = text(spec.get('dashed_means', '비동기·선택'), 'dashed_means', 1, 14)
    data = dict(scene='diagram', time=dict(unit='', end=end, steps=n), cues=cues, layers=out, edges=edges, groups=groups, steps=steps, highlight=hl, dashed_means=dm,
                types={k: v for k, v in NODE_TYPES.items() if v and any(n['type'] == k for x in out for n in x['nodes'])},
                captions=captions, rate=rate, labels=dict(data_kind=DIAGRAM_KINDS[data_kind]))

    def expect(T):
        return dict(state={'step': n if T >= n - 1e-9 else min(n - 1, math.floor(T + 1e-9))}, stats=[])
    samples = [round(i + 0.4, 4) for i in range(n)][:5] + [end]
    while len(samples) < 6:
        samples.append(end)
    checks = dict(end=end, samples=samples, annotations=[], expect=expect if live else None, resize_at=round(end / 2, 4), choreo=bool(cues))
    name = {x['id']: x['name'] for ly in out for x in ly['nodes']}
    head = ['구분', '항목', '설명']
    rows = [[f'구성 요소 · {ly["label"] or i + 1}', x['name'], x['sub'] or NODE_TYPES[x['type']] or '-'] for i, ly in enumerate(out) for x in ly['nodes']]
    rows += [['연결', f'{name[e["a"]]} → {name[e["b"]]}', (e['label'] or '-') + (' (점선)' if e['dashed'] else '')] for e in edges]
    route = lambda r: ' → '.join([name[edges[r[0]]['a']]] + [name[edges[i]['b']] for i in r])
    rows += [[f'단계 {x["mark"]}', ' · '.join(route(r) for r in x['paths']), x['text']] for x in steps]
    return dict(data=data, aria=f'{title}. {claim}', notes=f'근거: {source} ({DIAGRAM_KINDS[data_kind]}).', table=(head, rows),
                checks=checks, live=live, numeric=dict(steps=n), title=title)
