"""Browser quality gates for any live or static visual macro (Chromium via Playwright).

Mechanical stand-ins for the rules in references/visual-guidelines.md: they catch defects
(overlap, clipping, contrast, tiny text, unreadable captions, future annotations, broken
controls, no-JS fallback) but do not judge whether the picture explains well. Screenshots
at the sample times and both widths are written for that human/AI review.
Not a Confluence test: target-page script execution and PDF export stay unverified.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

BUDGET = {715: 520, 360: 600}
VISIBLE = "[...root.querySelectorAll('svg')].filter(s=>s.getBoundingClientRect().width>0)"
OVERLAP_JS = """(root)=>{const t=""" + VISIBLE + """.flatMap(s=>[...s.querySelectorAll('text')]).filter(e=>e.textContent.trim()).map(e=>{const r=e.getBoundingClientRect();return {s:e.textContent,x:r.left,y:r.top,r:r.right,b:r.bottom}}).filter(a=>a.r>a.x);
 const bad=[];for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++){const a=t[i],b=t[j],w=Math.min(a.r,b.r)-Math.max(a.x,b.x),h=Math.min(a.b,b.b)-Math.max(a.y,b.y);if(w>1.5&&h>1.5)bad.push([a.s,b.s,Math.round(w),Math.round(h)])}
 const box=root.getBoundingClientRect();const out=t.filter(a=>a.x<box.left-1||a.r>box.right+1).map(a=>a.s);return {bad,out}}"""
CONTRAST_JS = """(root)=>{const lum=c=>{const m=c.match(/\\d+(\\.\\d+)?/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4));return 0.2126*m[0]+0.7152*m[1]+0.0722*m[2]};
 const cr=c=>(1.05)/(lum(c)+0.05);const bad=[];
 for(const e of """ + VISIBLE + """.flatMap(s=>[...s.querySelectorAll('text, tspan')])){if(!e.textContent.trim())continue;const c=getComputedStyle(e).fill;if(/255, 255, 255/.test(c))continue;if(cr(c)<4.5)bad.push([e.textContent.slice(0,20),c])}
 for(const e of root.querySelectorAll('[data-ca-stats] span, [data-ca-stats] b, [data-ca-caption], summary, [data-ca-controls] button')){const c=getComputedStyle(e).color;if(cr(c)<4.5)bad.push([e.textContent.slice(0,20),c])}
 return bad}"""
COVER_JS = """(root)=>{const bad=[];for(const s of """ + VISIBLE + """){const all=[...s.querySelectorAll('*')];
 all.forEach((t,i)=>{if(t.tagName!=='text'||!t.textContent.trim())return;const a=t.getBoundingClientRect(),area=a.width*a.height;if(!area)return;
  for(let j=i+1;j<all.length;j++){const e=all[j];if(!/^(rect|path|circle|polygon|ellipse)$/.test(e.tagName))continue;const c=getComputedStyle(e);
   if(c.fill==='none'||Number(c.opacity)<0.2||Number(c.fillOpacity)<0.2)continue;const b=e.getBoundingClientRect();
   const w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
   if(w>0&&h>0&&w*h>0.3*area){bad.push([t.textContent.slice(0,20),e.tagName]);break}}});}return bad}"""
BOX_JS = """(root)=>{const bad=[];for(const s of """ + VISIBLE + """){const solid=[...s.querySelectorAll('[data-solid]')];
 for(const t of s.querySelectorAll('text[data-in], text[data-free]')){const a=t.getBoundingClientRect();if(!a.width)continue;
  if(t.dataset.in){const e=solid.find(x=>x.dataset.solid===t.dataset.in);if(!e)continue;const b=e.getBoundingClientRect();
   if(a.left<b.left-0.5||a.right>b.right+0.5||a.top<b.top-0.5||a.bottom>b.bottom+0.5)bad.push([t.textContent.slice(0,20),'sticks out of its box'])}
  else for(const e of solid){const b=e.getBoundingClientRect(),w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
   if(w>1&&h>1){bad.push([t.textContent.slice(0,20),'sits on box '+e.dataset.solid]);break}}}}return bad}"""
# Motion, stepped at 30 frames per wall second (playback rate included) through the whole timeline:
#  tokens - dots drawn with K.token keep an id while they move; the distance one id covers between two
#           frames is its speed in CSS px per second; above MOTION_MAX the reader cannot follow it;
#  wires  - connectors drawn with K.wire may not contain a diagonal segment;
#  loose  - a dot that moves without K.token (its speed would go unchecked). Markers drawn with K.follow
#           ride on the data (a line's head) and are exempt: a jump in the data is information.
# Measured on the article demos before choosing what to gate: their frames also contain large instant
# changes (state switches, loop restarts), so "instant change" is not gated - it did not separate them from ours.
MOTION_MAX = 480
MOTION_JS = """([maxv])=>{const L=root=>root.__caLive;const root=document.querySelector('[data-ca-prefix]'),C=L(root),svg=root.querySelector('svg[data-ca-live]');
 const k=svg.getBoundingClientRect().width/svg.viewBox.baseVal.width,rate=C.rate||(()=>1);let T=0,prev=null,pd=null,loose=[],fast=[],wires=[],top=0,n=0,frames=0,ids=new Set();
 while(true){C.seek(T);frames++;const cur={};
  for(const e of svg.querySelectorAll('[data-token]'))cur[e.dataset.token]=[+e.getAttribute('cx'),+e.getAttribute('cy')];
  if(prev)for(const id in cur){ids.add(id);if(!(id in prev))continue;const v=Math.hypot(cur[id][0]-prev[id][0],cur[id][1]-prev[id][1])*k*30;
   if(v>top)top=v;if(v>maxv&&fast.length<5)fast.push([id,Math.round(v),+T.toFixed(2)])}
  if(frames%8===1)for(const w of svg.querySelectorAll('[data-wire]')){const q=w.getAttribute('points').trim().split(/[\s,]+/).map(Number);
   for(let i=2;i+1<q.length;i+=2)if(Math.abs(q[i]-q[i-2])>0.6&&Math.abs(q[i+1]-q[i-1])>0.6&&wires.length<5)wires.push([+T.toFixed(2),q.slice(i-2,i+2)])}
  const dots=[...svg.querySelectorAll('circle:not([data-token]):not([data-follow])')].map(e=>[+e.getAttribute('cx'),+e.getAttribute('cy'),e.getAttribute('r')+e.getAttribute('fill')]);
  if(pd&&loose.length<5)for(const a of dots){if(pd.some(b=>b[2]===a[2]&&Math.abs(b[0]-a[0])<0.05&&Math.abs(b[1]-a[1])<0.05))continue;
   /* moved = a dot appeared next to one that vanished in the same frame (an added dot in a grid is not motion) */
   const gone=pd.filter(b=>b[2]===a[2]&&!dots.some(c=>c[2]===b[2]&&Math.abs(c[0]-b[0])<0.05&&Math.abs(c[1]-b[1])<0.05));
   const near=gone.map(b=>Math.hypot(a[0]-b[0],a[1]-b[1])).sort((x,y)=>x-y)[0];if(near<20){loose.push([a[2],+T.toFixed(2),+near.toFixed(1)]);break}}
  prev=cur;pd=dots;if(T>=C.end)break;T=Math.min(C.end,T+rate(T)/30)}
 return {max:Math.round(top),fast,wires,loose,tokens:ids.size,frames}}"""
MINFONT_JS = """(sel)=>{let m=99;for(const s of document.querySelectorAll(sel)){const r=s.getBoundingClientRect();if(!r.width)continue;const k=r.width/s.viewBox.baseVal.width;for(const t of s.querySelectorAll('text')){if(!t.textContent.trim())continue;m=Math.min(m,parseFloat(t.getAttribute('font-size'))*k)}}return m}"""
FIGURE_BOX_JS = """(s)=>{const r=s.getBoundingClientRect();return [...s.querySelectorAll('text')].filter(e=>e.textContent.trim()).filter(e=>{const b=e.getBoundingClientRect();
 return b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1}).map(e=>e.textContent.slice(0,30))}"""


def figure_problems(page) -> list[str]:
    """The exported figure.svg loaded alone in `page` (viewport = figure width): every text inside
    the figure, no overlapping or painted-over text, contrast >= 4.5:1."""
    body = page.locator('body')
    found = [('text outside the figure', page.locator('svg').first.evaluate(FIGURE_BOX_JS)),
             ('overlapping text', body.evaluate(OVERLAP_JS)['bad']), ('text painted over', body.evaluate(COVER_JS)),
             ('low contrast', body.evaluate(CONTRAST_JS)), ('box text', body.evaluate(BOX_JS))]
    return [f'figure.svg: {what} {v}' for what, v in found if v]


FONT = None   # set by run(font=...): forces one font family to test layout under other metrics


def wrap(fragment, width):
    box = f'<div style="width:{width}px;margin:0 auto">' if width else '<div>'
    force = f'<style>[data-ca-prefix],[data-ca-prefix] *{{font-family:"{FONT}"!important}}</style>' if FONT else ''
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + force + '</head><body style="margin:0">' + box + fragment + '</div></body></html>')


def close(a, b):
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    return abs(a - b) <= 0.051


def run(fragment: str, checks: dict, data: dict, out: Path, name: str, browser_path: str | None = None, browser=None, font: str | None = None) -> dict:
    """checks: {end, samples, annotations:[[label, t]], expect: callable(T)->{state, stats} | None, resize_at}.
    font: run every check with this font family forced (e.g. NanumGothic) to catch metric-dependent overlaps."""
    global FONT
    FONT = font
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)
    live = 'data-ca-runtime="live"' in fragment
    fails, rec = [], {'id': name, 'live': live, 'checks': {}, 'sha256': hashlib.sha256(fragment.encode()).hexdigest(), 'bytes': len(fragment.encode())}
    end = checks['end']; prefix = fragment.split('data-ca-prefix="')[1].split('"')[0]

    def fail(msg):
        fails.append(msg)

    def body(br):
        rec['browser'] = br.version
        ctx = br.new_context(viewport={'width': 800, 'height': 1000}); page = ctx.new_page(); errors, reqs = [], []
        page.on('pageerror', lambda e: errors.append(str(e))); page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('request', lambda r: reqs.append(r.url))
        root = page.locator('[data-ca-prefix]')
        seek = lambda t: page.evaluate('([p,t])=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.seek(t)', [prefix, t])
        state = lambda: page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state()', prefix)
        if live:
            page.set_content(wrap(fragment, 715)); page.wait_for_timeout(700)
            t1 = float(page.get_attribute('[data-ca-prefix]', 'data-ca-t')); page.wait_for_timeout(400); t2 = float(page.get_attribute('[data-ca-prefix]', 'data-ca-t'))
            if not 0 < t1 < t2 < end: fail(f'autoplay: clock did not advance from the start ({t1}, {t2})')
            rec['checks']['autoplay'] = [t1, t2]
        samples = checks['samples'] if live else [end]
        for width in (715, 360):
            page.set_viewport_size({'width': 800 if width == 715 else 360, 'height': 1000}); page.set_content(wrap(fragment, 715 if width == 715 else None)); page.wait_for_timeout(250)
            h = root.bounding_box()['height']; rec['checks'][f'height_{width}'] = round(h)
            if h > BUDGET[width]: fail(f'{width}px: height {h:.0f} > budget {BUDGET[width]}')
            if page.evaluate('document.documentElement.scrollWidth>innerWidth+1'): fail(f'{width}px: horizontal page overflow')
            for t in samples:
                if live: seek(t); page.wait_for_timeout(40)
                o = root.evaluate(OVERLAP_JS)
                if o['bad']: fail(f'{width}px T={t:g}: overlapping text {o["bad"][:3]}')
                if o['out']: fail(f'{width}px T={t:g}: text outside the block {o["out"][:3]}')
                cov = root.evaluate(COVER_JS)
                if cov: fail(f'{width}px T={t:g}: text painted over by a later shape {cov[:3]}')
                box = root.evaluate(BOX_JS)   # text belonging to a box stays inside it; free labels stay off boxes
                if box: fail(f'{width}px T={t:g}: {box[:3]}')
                bad = root.evaluate(CONTRAST_JS)
                if bad: fail(f'{width}px T={t:g}: text below 4.5:1 contrast {bad[:3]}')
                mf = page.evaluate(MINFONT_JS, 'svg[data-ca-static]')
                if mf < 9: fail(f'{width}px T={t:g}: text renders at {mf:.1f}px (< 9px)')
                if live and checks.get('expect'):
                    want = checks['expect'](t); st = state()
                    for k, v in want['state'].items():
                        if not close(st.get(k), v): fail(f'{width}px T={t:g}: browser {k}={st.get(k)} != model {v}')
                    nums = root.locator('[data-ca-stats] b').all_inner_texts()
                    if nums[:len(want['stats'])] != want['stats']: fail(f'{width}px T={t:g}: status numbers {nums} != model {want["stats"]}')
                if live:
                    cap = [c for c in data['captions'] if t >= c[0] - 1e-9]
                    if cap and cap[-1][2] not in root.locator('[data-ca-caption]').inner_text(): fail(f'T={t:g}: caption is not the event-bound one')
                root.screenshot(path=str(out / f'{name}-{width}-{t:g}.png'))
            rec['checks'][f'samples_{width}'] = len(samples)
            if live:   # transient collisions between the screenshot samples
                for k in range(1, 25):
                    t = end * k / 24; seek(t); o = root.evaluate(OVERLAP_JS)
                    if o['bad'] or o['out']: fail(f'{width}px T={t:.2f}: overlapping/clipped text {(o["bad"] or o["out"])[:3]}'); break
                rec['checks'][f'dense_overlap_{width}'] = 24
        if live:   # Confluence columns are rarely exactly 715 px: the same dense sweep at 600 px
            page.set_viewport_size({'width': 800, 'height': 1000}); page.set_content(wrap(fragment, 600)); page.wait_for_timeout(250)
            for k in range(0, 25):
                t = end * k / 24; seek(t); o = root.evaluate(OVERLAP_JS); bx = root.evaluate(BOX_JS)
                if o['bad'] or o['out'] or bx: fail(f'600px T={t:.2f}: overlapping/clipped text {(o["bad"] or o["out"] or bx)[:3]}'); break
            rec['checks']['dense_overlap_600'] = 25
        if live:   # motion: token speed and wire shape over the whole timeline, at 715 and 360 px
            for width in (715, 360):
                page.set_viewport_size({'width': 800 if width == 715 else 360, 'height': 1000}); page.set_content(wrap(fragment, 715 if width == 715 else None)); page.wait_for_timeout(200)
                m = page.evaluate(MOTION_JS, [MOTION_MAX]); rec['checks'][f'motion_{width}'] = {k: m[k] for k in ('max', 'tokens', 'frames')}
                if m['fast']: fail(f'{width}px: token faster than {MOTION_MAX}px/s {m["fast"][:3]}')
                if m['wires']: fail(f'{width}px: diagonal wire segment {m["wires"][:2]}')
                if m['loose']: fail(f'{width}px: a dot moves but is not drawn with K.token (speed unchecked) {m["loose"][:2]}')
        if live:
            page.set_viewport_size({'width': 800, 'height': 1000}); page.set_content(wrap(fragment, 715)); page.wait_for_timeout(200)
            for label, at in checks.get('annotations', []):
                seek(max(0, at - 0.012 * end)); before = root.locator('svg[data-ca-live]').inner_html()
                seek(min(end, at + 0.012 * end)); after = root.locator('svg[data-ca-live]').inner_html()
                if label in before: fail(f'"{label}" shown before its time {at:g}')
                if label not in after: fail(f'"{label}" missing after its time {at:g}')
            root.locator('[data-a="end"]').click()
            if abs(state()['T'] - end) > 1e-6: fail('controls: "최종 장면" did not jump to the end')
            root.locator('[data-a="restart"]').click(); page.wait_for_timeout(300); s1 = state()
            if not (s1['playing'] and 0 < s1['T'] < end): fail('controls: "처음부터" did not restart playback')
            root.locator('[data-a="play"]').click(); a = state()['T']; page.wait_for_timeout(250)
            if state()['T'] != a: fail('controls: pause did not stop the clock')
            root.locator('[data-a="play"]').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(250)
            if not state()['T'] > a: fail('controls: keyboard Enter did not resume')
            ra = checks.get('resize_at', end / 2); seek(ra); vb0 = root.locator('svg[data-ca-live]').get_attribute('viewBox').split()[2]
            page.evaluate('document.querySelector("[data-ca-prefix]").parentElement.style.width="400px"'); page.wait_for_timeout(250)
            vb1 = root.locator('svg[data-ca-live]').get_attribute('viewBox').split()[2]
            if abs(state()['T'] - ra) > 1e-6 or vb0 == vb1: fail('resize: clock or relayout broken')
            page.set_content(wrap(fragment, 715)); page.wait_for_timeout(400); page.pdf(path=str(out / f'{name}-print.pdf'))
            if abs(state()['T'] - end) > 1e-6: fail('print: final scene not shown')
            page.emulate_media(media='print')
            if not root.locator('[data-ca-controls]').is_hidden(): fail('print: controls visible')
            page.emulate_media(media='screen')
            b = fragment.replace(prefix, prefix + '-x'); page.set_content(wrap(fragment + b, 715)); page.wait_for_timeout(500)
            page.locator(f'[data-ca-prefix="{prefix}"] [data-a="play"]').click()
            x = page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state().T', prefix); y = page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state().T', prefix + '-x')
            page.wait_for_timeout(300)
            if page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state().T', prefix) != x or not page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state().T', prefix + '-x') > y:
                fail('two blocks on one page are not independent')
        else:
            page.set_content(wrap(fragment, 715)); page.pdf(path=str(out / f'{name}-print.pdf'))
        if errors: fail(f'page errors: {errors[:3]}')
        if [u for u in reqs if u.startswith(('http:', 'https:'))]: fail('external requests made')
        ctx.close()
        if live:
            ctx = br.new_context(viewport={'width': 800, 'height': 1000}, reduced_motion='reduce'); page = ctx.new_page(); page.set_content(wrap(fragment, 715)); page.wait_for_timeout(600)
            st = page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state()', prefix)
            if abs(st['T'] - end) > 1e-6 or st['playing']: fail('reduced motion: autoplayed or not at the final scene')
            ctx.close()
        for width in (715, 360):
            ctx = br.new_context(viewport={'width': 800 if width == 715 else 360, 'height': 900}, java_script_enabled=False); page = ctx.new_page()
            page.set_content(wrap(fragment, 715 if width == 715 else None))
            sel = 'svg[data-ca-live]' if width == 715 else 'svg[data-ca-narrow]'
            if not page.locator(sel).is_visible(): fail(f'no-JS {width}px: static scene not visible')
            mf = page.evaluate(MINFONT_JS, sel)
            if mf < 9: fail(f'no-JS {width}px: text renders at {mf:.1f}px')
            if data['captions'][-1][2] not in page.locator('[data-ca-caption]').inner_text(): fail('no-JS: final caption missing')
            page.locator('[data-ca-prefix]').screenshot(path=str(out / f'{name}-nojs-{width}.png')); ctx.close()

    if browser is not None:
        body(browser)
    else:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=browser_path, headless=True, args=['--no-sandbox'])
            try:
                body(br)
            finally:
                br.close()
    rec['failures'] = fails; rec['result'] = 'FAIL' if fails else 'PASS'
    return rec


def caption_report(data, end):
    """Reading time per caption at the default speed (pure Python; also run by the CLI)."""
    from monitoring_cases import caption_walls, caption_need
    walls = caption_walls(data['captions'], data['rate'], end)
    return [dict(caption=c[2], shown_s=round(w, 1), need_s=round(caption_need(c[2]), 1), ok=i == len(walls) - 1 or w + 1e-6 >= caption_need(c[2]))
            for i, (c, w) in enumerate(zip(data['captions'], walls))]
