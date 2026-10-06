"""compose: a layout tree of containers and parts with links and steps (visuals/live/scenes/compose.js); concept forms are presets on it."""
from __future__ import annotations
import choreo
from model import DEFAULT_SPEED, caption_need
from kinds.common import CIRCLED, DIAGRAM_KINDS, common, fill, need, only, text
from kinds.diagram import NODE_ID, ROLE_TONES


# Composition engine (docs/design/motion-concept-architecture.md, section 12): a figure is a tree of layout
# containers and parts. Containers nest; every part (element, connector, annotation) works in every container.
# The scene (visuals/live/scenes/compose.js) lays the tree out at the column width and routes connectors
# orthogonally; each part registers its boxes and text for the shared gates. Earlier fixed forms (concept
# compare / stack / sequence) are presets that expand into a tree here.
LAYOUTS = ('row', 'column', 'grid', 'stack', 'split', 'lifelines')
SHAPES = ('box', 'pill', 'cylinder', 'doc')
STATES = ('normal', 'selected', 'muted', 'error', 'ok')
LINK_STYLES = ('flow', 'reply', 'hidden', 'fail', 'none')
BADGES = ('ok', 'bad', 'warn', 'info')
STEP_MIN = 1.0      # model seconds per step (rate 0.5: 1.6 s on screen at the default 1.25x)
COMPOSE_RATE = 0.5
HOLD = 1.0          # settled tail after the last step: the last connector's dot finishes inside it


def compose_tree(root, ids):
    """Validate and normalise the layout tree. Returns (tree, elements in document order, containers)."""
    elems, conts, path = [], [], []
    tone = lambda v, nm: v if v is None or v in ROLE_TONES else need(False, f'{nm}: one of {list(ROLE_TONES)}')

    def take_id(n, nm, auto):
        i = n.get('id')
        if i is None:
            i = auto
        else:
            need(isinstance(i, str) and NODE_ID.match(i), f'{nm}.id: letters, digits, _ or - (max 24), starting with a letter')
        need(i not in ids, f'{nm}.id: "{i}" used twice')
        ids[i] = nm
        return i

    def element(n, nm, in_stack=False, in_life=False):
        only(n, ('id', 'name', 'sub', 'shape', 'tone', 'state', 'code', 'badge', 'bubble', 'size', 'grow', 'dashed', 'bar'), nm)
        e = dict(t='e', auto=n.get('id') is None, id=take_id(n, nm, f'e{len(elems)}'), name=text(n.get('name'), f'{nm}.name', 1, 18 if in_stack else 16),
                 sub=text(n['sub'], f'{nm}.sub', 1, 28 if in_stack else 22) if n.get('sub') else '')
        shp = n.get('shape', 'box'); need(shp in SHAPES, f'{nm}.shape: one of {list(SHAPES)}')
        st = n.get('state', 'normal'); need(st in STATES, f'{nm}.state: one of {list(STATES)}')
        code = n.get('code') or []
        if isinstance(code, str):
            code = code.split('\n')
        need(isinstance(code, list) and len(code) <= 5 and all(isinstance(c, str) and len(c) <= 30 for c in code),
             f'{nm}.code: up to 5 lines of at most 30 characters (a JSON or code fragment)')
        bd = n.get('badge')
        if bd is not None:
            only(bd, ('text', 'kind'), f'{nm}.badge')
            need(bd.get('kind', 'info') in BADGES, f'{nm}.badge.kind: one of {list(BADGES)}')
            bd = dict(text=text(bd.get('text'), f'{nm}.badge.text', 1, 10), kind=bd.get('kind', 'info'))
        size = n.get('size', 1); need(size in (1, 2, 3), f'{nm}.size: 1, 2 or 3 (relative height in a stack)')
        grow = n.get('grow', 1); need(grow in (1, 2, 3), f'{nm}.grow: 1, 2 or 3 (relative width in a row)')
        dsh = n.get('dashed', False); need(isinstance(dsh, bool), f'{nm}.dashed: true for something outside your control (an external service)')
        bar = n.get('bar'); need(bar is None or (isinstance(bar, (int, float)) and 0 <= bar <= 1), f'{nm}.bar: 0-1, a relative amount shown as a bar (not a measured number)')
        e.update(shape=shp, tone=tone(n.get('tone'), f'{nm}.tone') or (path[-1] if path else 'blue'), sts=[st], code=code,
                 badge=bd, bds=[bd], bubble=text(n['bubble'], f'{nm}.bubble', 1, 26) if n.get('bubble') else '', size=size, grow=grow,
                 dashed=dsh, bar=None if bar is None else round(float(bar), 3))
        need(not (in_life and (code or bd or n.get('bubble') or bar is not None)), f'{nm}: lifeline actors take a name and tone only')
        elems.append(e)
        return e

    def node(n, nm, depth):
        need(isinstance(n, dict), f'{nm}: object required')
        if 'layout' not in n:
            return element(n, nm)
        need(depth <= 4, f'{nm}: containers nest at most 4 deep')
        L = n.get('layout'); need(L in LAYOUTS, f'{nm}.layout: one of {list(LAYOUTS)}')
        only(n, ('layout', 'id', 'items', 'label', 'tone', 'frame', 'note', 'banner', 'span', 'sep', 'bracket', 'free', 'arrow', 'cols', 'messages', 'grow'), nm)
        c = dict(t='c', L=L, auto=n.get('id') is None, id=take_id(n, nm, f'k{len(conts)}'))
        conts.append(c)
        ct = tone(n.get('tone'), f'{nm}.tone')
        fr = n.get('frame'); need(fr in (None, False, 'solid', 'dashed'), f'{nm}.frame: "solid" (a group) or "dashed" (a boundary)')
        bn = n.get('banner')
        if bn is not None:
            if isinstance(bn, str):
                bn = dict(text=bn)
            only(bn, ('text', 'tone'), f'{nm}.banner')
            bn = dict(text=text(bn.get('text'), f'{nm}.banner.text', 1, 40), tone=tone(bn.get('tone'), f'{nm}.banner.tone') or 'red')
        grow = n.get('grow', 1); need(grow in (1, 2, 3), f'{nm}.grow: 1, 2 or 3')
        c.update(label=text(n['label'], f'{nm}.label', 1, 18) if n.get('label') else '', tone=ct or (path[-1] if path else 'gray'),
                 frame=fr or '', note=text(n['note'], f'{nm}.note', 1, 40) if n.get('note') else '', banner=bn,
                 span=text(n['span'], f'{nm}.span', 1, 24) if n.get('span') else '', grow=grow)
        for k, allowed in (('sep', ('row',)), ('bracket', ('column', 'stack')), ('free', ('stack',)), ('arrow', ('split',)),
                           ('cols', ('grid',)), ('messages', ('lifelines',))):
            need(n.get(k) is None or L in allowed, f'{nm}.{k}: only for layout {" / ".join(allowed)}')
        c['sep'] = text(n['sep'], f'{nm}.sep', 1, 8) if n.get('sep') else ''
        c['bracket'] = text(n['bracket'], f'{nm}.bracket', 1, 12) if n.get('bracket') else ''
        c['free'] = text(n['free'], f'{nm}.free', 1, 14) if n.get('free') else ''
        c['arrow'] = text(n['arrow'], f'{nm}.arrow', 1, 10) if n.get('arrow') else ''
        items = n.get('items')
        lim = {'row': (1, 5), 'column': (1, 7), 'grid': (2, 12), 'stack': (2, 7), 'split': (2, 3), 'lifelines': (2, 4)}[L]
        need(isinstance(items, list) and lim[0] <= len(items) <= lim[1], f'{nm}.items: {lim[0]}-{lim[1]} for a {L}')
        if L == 'grid':
            cols = n.get('cols', 3); need(cols in (2, 3, 4), f'{nm}.cols: 2, 3 or 4'); c['cols'] = cols
        path.append(c['tone'] if ct else (path[-1] if path else 'blue'))
        if L in ('stack', 'lifelines'):
            c['kids'] = [element(x if isinstance(x, dict) else need(False, f'{nm}.items[{i}]: object'), f'{nm}.items[{i}]', L == 'stack', L == 'lifelines')
                         for i, x in enumerate(items)]
            need(all('layout' not in x for x in items), f'{nm}.items: a {L} holds elements only')
        else:
            c['kids'] = [node(x, f'{nm}.items[{i}]', depth + 1) for i, x in enumerate(items)]
        if L == 'split':
            for i, k in enumerate(c['kids']):
                need(k['t'] == 'c', f'{nm}.items[{i}]: each side of a split is a container (e.g. a column with a label)')
        path.pop()
        if L == 'lifelines':
            msgs = n.get('messages'); need(isinstance(msgs, list) and 1 <= len(msgs) <= 8, f'{nm}.messages: 1-8, in order')
            loc = {k['id']: i for i, k in enumerate(c['kids'])}; mo = []
            for k, m in enumerate(msgs):
                mm = f'{nm}.messages[{k}]'; only(m, ('from', 'to', 'text', 'style'), mm)
                need(m.get('from') in loc and m.get('to') in loc, f'{mm}: from/to must be ids of this lifeline\'s actors ({", ".join(loc)})')
                stl = m.get('style', 'solid'); need(stl in ('solid', 'dashed'), f'{mm}.style: solid (request) or dashed (reply)')
                mo.append(dict(a=loc[m['from']], b=loc[m['to']], text=text(m.get('text'), f'{mm}.text', 1, 24), dashed=stl == 'dashed', mark=CIRCLED[k], key=f'{c["id"]}.m{k}'))
            c['msgs'] = mo
        return c

    tree = node(root, 'root', 0)
    need(len(elems) <= 24, f'compose: {len(elems)} elements; at most 24 (split the idea into two figures)')
    return tree, elems, conts


def compose_build(spec, root, links, steps, table_head=None, extra_rows=None, opts=None):
    """Shared body of the compose kind and its presets: validation, default choreography, captions, checks.
    opts (presets): rate (model s per wall s), step (model s per step), live, step_list, legend, notes."""
    kind, title, claim, source, data_kind, motion = common(spec)
    opts = opts or {}
    ids = {}
    tree, elems, conts = compose_tree(root, ids)
    E = {e['id']: e for e in elems}
    C = {c['id']: c for c in conts}
    under = {}   # container id -> element ids beneath it

    def collect(n):
        if n['t'] == 'e':
            return [n['id']]
        out = [i for k in n['kids'] for i in collect(k)]
        under[n['id']] = out
        return out
    collect(tree)
    lk = []
    for k, l in enumerate(links or []):
        nm = f'links[{k}]'; only(l, ('id', 'from', 'to', 'label', 'style', 'via', 'token'), nm)
        a, b = l.get('from'), l.get('to')
        need(a in E and b in E and a != b, f'{nm}: from/to must be two different element ids ({", ".join(E)})')
        st = l.get('style', 'flow'); need(st in LINK_STYLES, f'{nm}.style: one of {list(LINK_STYLES)} (flow = request/data, reply = answer, hidden = a dependency not visible in code, fail = broken, none = explicitly no connection)')
        via = l.get('via'); need(via in (None, 'left', 'right'), f'{nm}.via: left or right (route around the side, e.g. a loop back)')
        lid = l.get('id', f'L{k}'); need(isinstance(lid, str) and NODE_ID.match(lid) and lid not in ids, f'{nm}.id: unique letters/digits')
        ids[lid] = nm
        tok = l.get('token', st == 'flow'); need(isinstance(tok, bool), f'{nm}.token: true or false')
        lk.append(dict(id=lid, a=a, b=b, label=text(l['label'], f'{nm}.label', 1, 16) if l.get('label') else '', style=st, via=via or '', token=tok))
    need(len(lk) <= 24, 'links: at most 24')
    by_pair = {(l['a'], l['b']): l['id'] for l in lk}
    lifeline_msgs = [m for c in conts if c['L'] == 'lifelines' for m in c['msgs']]

    # --- steps: what appears, changes and travels when -----------------------------------------------------
    live = (motion != 'none') if opts.get('live') is None else opts['live']
    show, sets, caps = {}, [], []
    if steps is not None:
        need(isinstance(steps, list) and 1 <= len(steps) <= 6, 'steps: 1-6, in order')
        units = []
        for k, st in enumerate(steps):
            nm = f'steps[{k}]'; only(st, ('show', 'set', 'caption', 'path', 'paths'), nm)
            sh = st.get('show') or []
            need(isinstance(sh, list) and all(x in ids for x in sh), f'{nm}.show: ids of elements, containers, links or lifeline messages ({", ".join(list(ids)[:12])}...)')
            se = st.get('set') or {}
            need(isinstance(se, dict) and all(x in E for x in se), f'{nm}.set: {{element id: state}} or {{id: {{"state": ..., "badge": {{...}}}}}}')
            sv = {}
            for x, v in se.items():
                if isinstance(v, dict):
                    only(v, ('state', 'badge'), f'{nm}.set.{x}')
                    bd = v.get('badge')
                    if bd is not None:
                        only(bd, ('text', 'kind'), f'{nm}.set.{x}.badge'); need(bd.get('kind', 'info') in BADGES, f'{nm}.set.{x}.badge.kind: one of {list(BADGES)}')
                        bd = dict(text=text(bd.get('text'), f'{nm}.set.{x}.badge.text', 1, 10), kind=bd.get('kind', 'info'))
                    v = (v.get('state', 'normal'), bd)
                else:
                    v = (v, None)
                need(v[0] in STATES, f'{nm}.set.{x}: state one of {list(STATES)}')
                sv[x] = v
            need(not ('path' in st and 'paths' in st), f'{nm}: give "path" (one route) or "paths" (routes at the same time)')
            pths = [st['path']] if 'path' in st else st.get('paths') or []
            need(isinstance(pths, list) and len(pths) <= 3, f'{nm}.paths: 1-3 routes')
            routes = []
            for pth in pths:
                need(isinstance(pth, list) and len(pth) >= 2 and all(x in E for x in pth), f'{nm}.path: two or more element ids')
                for a, b in zip(pth, pth[1:]):
                    need((a, b) in by_pair, f'{nm}.path: no connection {a} -> {b}; add it to links (direction matters)')
                routes.append([by_pair[(a, b)] for a, b in zip(pth, pth[1:])])
            need(sh or sv or routes, f'{nm}: show something, set a state or follow a path')
            for x in list(sh) + list(sv):   # a step names the part it is about: only names the author gave, never the whole figure
                part = E.get(x) or C.get(x)
                need(not (part and part.get('auto')), f'{nm}: "{x}" is a name the engine made up; give that part an "id" and use it '
                     '(made-up names follow the tree order and silently point at the wrong part)')
                need(x != tree['id'], f'{nm}: "{x}" is the whole figure; name the part this step is about')
            units.append(dict(show=sh, set=sv, routes=routes, nodes=[x for p_ in pths for x in p_],
                              caption=text(fill(text(st['caption'], f'{nm}.caption', 2, 80), {}, f'{nm}.caption'), f'{nm}.caption', 2, 60) if st.get('caption') else ''))
    else:
        units = []
        if tree['L'] == 'lifelines':
            units.append(dict(show=[tree['id']], set={}, routes=[], nodes=[], caption=''))
            units += [dict(show=[m['key']], set={}, routes=[], nodes=[], caption='') for m in tree['msgs']]
        else:
            kids = tree['kids'][::-1] if tree['L'] == 'stack' else tree['kids']   # a stack is built from the ground up
            units = [dict(show=[k['id']], set={}, routes=[], nodes=[], caption='') for k in kids]
            if tree['L'] == 'stack':
                units[0]['show'] = [tree['id']] + units[0]['show']
    R_ = opts.get('rate', COMPOSE_RATE)
    slist = bool(opts.get('step_list'))
    # step lengths: long enough for the step's caption at the default speed (captions bind to steps); a step list
    # in the picture is read at leisure, so it does not stretch the step
    base = 0.4 if steps is None and tree['L'] == 'stack' else opts.get('step', STEP_MIN)
    lens = [max(base, caption_need(u['caption']) * R_ * DEFAULT_SPEED) if u['caption'] and not slist else base for u in units]
    t0s = [round(sum(lens[:k]), 4) for k in range(len(units))]
    total = round(sum(lens), 4)
    for k, u in enumerate(units):
        for x in u['show']:
            if x in E or any(x == l['id'] for l in lk) or any(x == m['key'] for m in lifeline_msgs):
                show.setdefault(x, t0s[k])
            if x in C:
                show.setdefault(x, t0s[k])
                for i in under[x]:
                    show.setdefault(i, t0s[k])
    listed = set(show)           # parts a step brings in (they enter); everything else is context, there from the start
    for e in elems:
        show.setdefault(e['id'], 0.0)
    for c in conts:              # a frame or annotation appears with its first element
        show.setdefault(c['id'], min([show[i] for i in under[c['id']]] or [0.0]))
        show[c['id']] = min(show[c['id']], min([show[i] for i in under[c['id']]] or [show[c['id']]]))
    for c in conts:              # messages not listed follow their lifelines one after another
        for k, m in enumerate(c.get('msgs', [])):
            show.setdefault(m['key'], show[c['id']] + 0.8 * R_ + 1.0 * R_ * k)
    for l in lk:                 # a connector is drawn once both ends are there (a context link between context parts is just there)
        moving = steps is None or l['id'] in listed or l['a'] in listed or l['b'] in listed
        if moving:
            listed.add(l['id'])
        show[l['id']] = max(show.get(l['id'], 0), max(show[l['a']], show[l['b']]) + (0.7 * R_ if moving else 0))
    for k, u in enumerate(units):
        for x, (v, bd) in u['set'].items():
            E[x]['sts'].append(v); E[x]['bds'].append(bd if bd is not None else E[x]['bds'][-1])
            sets.append((x, len(E[x]['sts']) - 1, t0s[k] + 0.5 * R_))
    # correspondence: every captioned step points at one part of the picture (the first thing it shows, changes or
    # follows); the engine keeps it to light that part up while the step's caption or list row is current. The
    # pairing is shown by timing, never by numbers drawn on the picture.
    marks = []
    for k, u in enumerate(units):
        if steps is None or not u['caption']:
            continue
        tgt = (u['show'] or list(u['set']) or [r[0] for r in u['routes']])[0]
        kind_ = 'e' if tgt in E else 'c' if tgt in C else 'm' if any(tgt == m['key'] for m in lifeline_msgs) else 'l'
        marks.append(dict(target=tgt, kind=kind_, k=k, mark=CIRCLED[len(marks)] if len(marks) < len(CIRCLED) else f'{len(marks) + 1}.', t=t0s[k]))
        u['mark'] = marks[-1]['mark']
        if not slist:
            caps.append([t0s[k], u['mark'], u['caption']])
    end = round(max(total, max(show.values()) + 1.2 * R_) + 2.7 * R_, 4)
    rate = [[0, R_]] if live else [[0, 1]]
    cues = []
    focus = {mk['k']: mk['target'] for mk in marks}   # the part each captioned step is about stands out during it
    for k, u in enumerate(units):
        u['hot_l'] = {lid for r in u['routes'] for lid in r} | ({focus[k]} if focus.get(k) in {l['id'] for l in lk} else set())
        u['hot_n'] = set(u['nodes']) | ({focus[k]} if focus.get(k) in E else set())
    hot_l = {lid for u in units for lid in u['hot_l']}
    hot_n = {x for u in units for x in u['hot_n']}
    times = t0s + [total]
    if live:
        order = sorted(set(list(E) + list(C)), key=lambda i: show[i])
        for i in order:
            if steps is None or i in listed or (i in C and any(x in listed for x in under[i])):
                cues += choreo.levels(i, 'on', [1], [show[i]], rate)
        for i in sorted([l['id'] for l in lk] + [m['key'] for m in lifeline_msgs], key=lambda i: show[i]):
            if steps is None or i in listed or i in [m['key'] for m in lifeline_msgs]:
                cues.append(choreo.cue(i, 'reveal', show[i], 0.5, 0, 1, 'inOut', rate))
        for x, lvl, t in sets:
            cues.append(choreo.cue(x, 'act', t, 0.3, lvl - 1, lvl, 'inOut', rate))
        for lid in hot_l:        # the current step's route stands out, then falls back
            cues += choreo.levels(lid, 'level', [1 if lid in u['hot_l'] else 0 for u in units] + [0], times, rate)
        for x in hot_n:
            lv = choreo.levels(x, 'level', [1 if x in u['hot_n'] else 0 for u in units] + [0], times, rate)
            cues += lv + [choreo.cue(x, 'pop', c[2], 0.4, 0, 1, 'linear', rate) for c in lv if c[6] > c[5]]
        if slist:
            for n, mk in enumerate(marks):
                k = mk['k']
                cues += choreo.levels(f'sl{n}', 'level', [2 if k == j else 1 if k < j else 0 for j in range(len(units))] + [1], times, rate)
        cues = choreo.validate(cues, end)
    captions = ([[0.0, '', claim]] if not caps or caps[0][0] > 0 else []) + caps if live else [[end, '', (caps[-1][2] if caps else claim)]]
    if not live:
        for e in elems:
            e['sts'] = [e['sts'][-1]]; e['bds'] = [e['bds'][-1]]
    if steps is None:
        for c in captions:
            c[1] = ''
    legend = opts.get('legend') if opts.get('legend') is not None else spec.get('legend')
    lg = []
    for i, x in enumerate(legend or []):
        nm = f'legend[{i}]'; only(x, ('tone', 'style', 'shape', 'dashed', 'text'), nm)
        need(x.get('tone') in (None,) + ROLE_TONES and x.get('style') in (None,) + LINK_STYLES and x.get('shape') in (None,) + SHAPES, f'{nm}: tone, style or shape with a text')
        lg.append(dict(tone=x.get('tone') or '', style=x.get('style') or '', shape=x.get('shape') or '', dashed=bool(x.get('dashed')), text=text(x.get('text'), f'{nm}.text', 1, 20)))
    need(len(lg) <= 5, 'legend: at most 5 entries')
    data = dict(scene='compose', tree=tree, links=lk, time=dict(unit='', end=end), cues=cues, captions=captions, rate=rate,
                labels=dict(data_kind=DIAGRAM_KINDS[data_kind]), show={k: round(v, 4) for k, v in show.items()},
                paths=[dict(t0=t0s[k], t1=round(t0s[k] + lens[k], 4), routes=u['routes']) for k, u in enumerate(units) if u['routes']] if live else [],
                steps=dict(t0=t0s, total=total, n=len(units)) if steps is not None and live else None,
                slist=[dict(mark=mk['mark'], text=units[mk['k']]['caption']) for mk in marks] if slist else [], legend=lg,
                marks=[{k: v for k, v in mk.items() if k != 'k'} for mk in marks])
    # accessible table: every part in reading order, then connectors and steps
    names = {e['id']: e['name'] for e in elems}
    rows = list(extra_rows) if extra_rows is not None else None
    if rows is None:
        rows = []

        def walk(n, trail):
            if n['t'] == 'e':
                st = n['sts']
                desc = ' · '.join(x for x in (n['sub'], ' → '.join(dict.fromkeys(b['text'] for b in n['bds'] if b)), ' / '.join(n['code']),
                                              ('상태 ' + ' → '.join(STATE_KO[s] for s in st)) if st != ['normal'] else '',
                                              ('말풍선: ' + n['bubble']) if n['bubble'] else '', '외부' if n['dashed'] else '',
                                              f'상대적 양 {round(n["bar"] * 100)}%' if n['bar'] is not None else '') if x)
                rows.append([' · '.join(trail) or '요소', n['name'], desc or '-'])
                return
            lab = n['label'] or ''
            for k in n['kids']:
                walk(k, trail + ([lab] if lab else []))
            for m in n.get('msgs', []):
                rows.append([m['mark'], f'{n["kids"][m["a"]]["name"]} → {n["kids"][m["b"]]["name"]}', m['text'] + (' (응답)' if m['dashed'] else '')])
            for nm_, v in (('설명', n['note']), ('강조', n['banner']['text'] if n['banner'] else ''), ('범위', n['span']), ('경계', n['sep']), ('괄호', n['bracket'])):
                if v:
                    rows.append([(lab or '묶음') + ' · ' + nm_, v, '-'])
        walk(tree, [])
        for l in lk:
            rows.append(['연결', f'{names[l["a"]]} → {names[l["b"]]}', (l['label'] or '-') + ('' if l['style'] == 'flow' else f' ({LINK_KO[l["style"]]})')])
        if steps is not None:
            lab_of = {l['id']: l for l in lk}
            for k, u in enumerate(units):
                what = ', '.join(names.get(x) or C.get(x, {}).get('label') or x for x in u['show'])
                ch = ', '.join(f'{names[x]} → {STATE_KO[v]}' for x, (v, _) in u['set'].items())
                rt = ' · '.join(' → '.join([names[lab_of[r[0]]['a']]] + [names[lab_of[i]['b']] for i in r]) for r in u['routes'])
                rows.append([f'단계 {CIRCLED[k]}', ' / '.join(v for v in (rt, what, ch) if v), u['caption'] or '-'])
    n_s = len(units)
    samples = [round(min(end, t0s[k] + lens[k] * 0.7), 4) for k in range(n_s)][:5] + [end]
    while len(samples) < 6:
        samples.append(end)

    def expect(T):   # the browser's current step (scene probe) equals the model's
        return dict(state={'step': n_s if T >= total - 1e-9 else max([k for k in range(n_s) if t0s[k] <= T + 1e-9] or [0])}, stats=[])
    checks = dict(end=end, samples=samples, annotations=[], expect=expect if (live and steps is not None) else None,
                  resize_at=round(end / 2, 4), choreo=live and bool(cues))
    return dict(data=data, aria=f'{title}. {claim}', notes=opts.get('notes') or f'출처: {source} ({DIAGRAM_KINDS[data_kind]}). 개념도이며 수치를 나타내지 않습니다.',
                table=(table_head or ['묶음', '요소', '설명'], rows), checks=checks, live=live,
                numeric=dict(elements=len(elems), containers=len(conts), links=len(lk), steps=len(units)), title=title)


STATE_KO = {'normal': '보통', 'selected': '선택', 'muted': '흐림', 'error': '오류', 'ok': '정상'}
LINK_KO = {'flow': '흐름', 'reply': '응답', 'hidden': '숨은 의존', 'fail': '실패', 'none': '연결 없음'}


def compose_data(spec):
    """Kind "compose": {root: layout tree, links: [...], steps: [...]}; see references/visual-specs.md."""
    common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'root', 'links', 'steps', 'step_list', 'legend'), 'compose spec')
    need(spec.get('step_list') in (None, True, False), 'step_list: true keeps the numbered step captions in the picture (print and no-JS keep the story)')
    need(isinstance(spec.get('root'), dict) and 'layout' in spec['root'], 'root: a layout container ({"layout": "row", "items": [...]})')
    return compose_build(spec, spec['root'], spec.get('links'), spec.get('steps'), opts=dict(step_list=spec.get('step_list')))
