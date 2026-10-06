"""Before/after sheets at identical model times and widths, for human review. Run from repo root.

Usage: python tests/compare_baseline.py --baseline dist/baseline [--current dist/monitoring-suite]
       [--cases a,b] [--output dist/compare]

Model time -> capture: a live macro is seeked to T; a CSS macro is paused at
wall = duration x (0.06 + 0.8 x T / end), the CSS tier's model-to-wall mapping.
Sample times come from the current case's live gate (monitoring_cases.live_checks).
Writes <case>-<width>.png sheets (left: baseline, right: current). Judges nothing.
"""
from __future__ import annotations
from pathlib import Path
import argparse,io,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
from monitoring_cases import live_checks,LIVE_BUILDERS

ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--current',type=Path,default=ROOT/'dist/monitoring-suite')
ap.add_argument('--cases');ap.add_argument('--output',type=Path,default=ROOT/'dist/compare');ap.add_argument('--browser')
opt=ap.parse_args();opt.output.mkdir(parents=True,exist_ok=True)
CASES={c['id']:c for c in json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases']}
ids=opt.cases.split(',') if opt.cases else [i for i,c in CASES.items() if i in LIVE_BUILDERS]

def wrap(fragment,width):
    box=f'width:{width}px;margin:0 auto' if width>400 else ''
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;background:#fff"><div style="{box}">{fragment}</div></body></html>'

def capture(page,fragment,width,t,end):
    page.set_viewport_size({'width':800 if width>400 else width,'height':1000});page.set_content(wrap(fragment,width));page.wait_for_timeout(250)
    if 'data-ca-runtime="live"' in fragment:
        page.evaluate('(t)=>document.querySelector("[data-ca-prefix]").__caLive.seek(t)',t)
    else:
        m=re.search(r'--duration:([0-9.]+)s;',fragment);duration=float(m[1]) if m else 14.4
        page.evaluate('(ms)=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=ms})',duration*1000*(0.06+0.8*t/end))
    page.wait_for_timeout(50)
    return Image.open(io.BytesIO(page.locator('[data-ca-prefix]').first.screenshot()))

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=opt.browser,headless=True,args=['--no-sandbox']);page=browser.new_page()
    summary=[]
    for cid in ids:
        old=opt.baseline/cid/'macro.html';new=opt.current/cid/'macro.html'
        if not old.is_file() or not new.is_file():print('SKIP',cid,'missing macro');continue
        chk=live_checks(cid,CASES[cid]['params']);a,b=old.read_text(encoding='utf8'),new.read_text(encoding='utf8')
        for width in (715,360):
            rows=[(t,capture(page,a,width,t,chk['end']),capture(page,b,width,t,chk['end'])) for t in chk['samples']]
            heights=(rows[0][1].height,rows[0][2].height)
            # Long baselines are cropped to the current height x 1.6 so sheets stay readable; full height is reported.
            cap=int(max(r[2].height for r in rows)*1.6)
            colw=max(r[1].width for r in rows)+max(r[2].width for r in rows)+30
            sheet=Image.new('RGB',(colw,sum(min(max(r[1].height,r[2].height),cap)+28 for r in rows)),'white');d=ImageDraw.Draw(sheet);y=0
            for t,x,z in rows:
                d.text((6,y+6),f'T = {t:g} (model)   left: baseline  right: current',fill='black');y+=24
                sheet.paste(x.crop((0,0,x.width,min(x.height,cap))),(0,y));sheet.paste(z,(x.width+30,y));y+=min(max(x.height,z.height),cap)+4
            sheet.save(opt.output/f'{cid}-{width}.png');summary.append(dict(id=cid,width=width,samples=chk['samples'],height_before=heights[0],height_after=heights[1]))
            print('SHEET',cid,width,'height',heights[0],'->',heights[1])
    browser.close()
(opt.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
