"""Live-runtime browser quality gates (JavaScript enabled). Run from repository root.

Checks are mechanical stand-ins for review rules in references/live-runtime.md; they do
not judge aesthetics. Screenshots at fixed model times are written for human review.
Not a Confluence test: target-page script execution and PDF export remain unverified.
"""
from __future__ import annotations
from pathlib import Path
import argparse,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright
from monitoring_cases import build_case,live_checks,LIVE_BUILDERS
from reference_scene import document
ap=argparse.ArgumentParser();ap.add_argument('--browser');ap.add_argument('--output',type=Path,default=ROOT/'dist/live')
opt=ap.parse_args();OUT=opt.output;SHOTS=OUT/'screenshots';SHOTS.mkdir(parents=True,exist_ok=True)
CASES=[c for c in json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases'] if c.get('runtime')=='live']
BUDGET={715:520,360:600}
report={'confluence_verified':False,'tested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'cases':[]}

OVERLAP_JS="""(root)=>{const t=[...root.querySelectorAll('svg[data-ca-live] text')].map(e=>{const r=e.getBoundingClientRect();return {s:e.textContent,x:r.left,y:r.top,r:r.right,b:r.bottom}}).filter(a=>a.r>a.x);
 const bad=[];for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++){const a=t[i],b=t[j],w=Math.min(a.r,b.r)-Math.max(a.x,b.x),h=Math.min(a.b,b.b)-Math.max(a.y,b.y);if(w>1.5&&h>1.5)bad.push([a.s,b.s,Math.round(w),Math.round(h)])}
 const box=root.getBoundingClientRect();const out=t.filter(a=>a.x<box.left-1||a.r>box.right+1).map(a=>a.s);return {bad,out}}"""
CONTRAST_JS="""(root)=>{const lum=c=>{const m=c.match(/\\d+(\\.\\d+)?/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4));return 0.2126*m[0]+0.7152*m[1]+0.0722*m[2]};
 const cr=c=>{const l=lum(c);return (1.05)/(l+0.05)};const bad=[];
 for(const e of root.querySelectorAll('svg[data-ca-live] text, svg[data-ca-live] tspan')){if(!e.textContent.trim())continue;const c=getComputedStyle(e).fill;if(/255, 255, 255/.test(c))continue;if(cr(c)<4.5)bad.push([e.textContent.slice(0,20),c])}
 for(const e of root.querySelectorAll('[data-ca-stats] span, [data-ca-stats] b, [data-ca-caption], summary, [data-ca-controls] button')){const c=getComputedStyle(e).color;if(cr(c)<4.5)bad.push([e.textContent.slice(0,20),c])}
 return bad}"""
MINFONT_JS="""(sel)=>{let m=99;for(const s of document.querySelectorAll(sel)){const r=s.getBoundingClientRect();if(!r.width)continue;const k=r.width/s.viewBox.baseVal.width;for(const t of s.querySelectorAll('text')){if(!t.textContent.trim())continue;m=Math.min(m,parseFloat(t.getAttribute('font-size'))*k)}}return m}"""
def wrap(fragment,width):
 return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0">'+(
  f'<div style="width:{width}px;margin:0 auto">' if width else '<div>')+fragment+'</div></body></html>'
def seek(page,prefix,t):page.evaluate('([p,t])=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.seek(t)',[prefix,t])
def live_state(page,prefix):return page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state()',prefix)
def close(a,b):
 return all(close(x,y) for x,y in zip(a,b)) and len(a)==len(b) if isinstance(a,list) else abs(a-b)<=0.051
def model_matches(st,want):return all(close(st[k],v) for k,v in want.items())
def stats_numbers(page,prefix):return page.locator(f'[data-ca-prefix="{prefix}"] [data-ca-stats] b').all_inner_texts()

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=opt.browser,headless=True,args=['--no-sandbox'])
 report['browser']=browser.version
 for c in CASES:
  rec={'id':c['id'],'checks':{}};prefix='ca-live-b';frag,model=build_case(c,prefix,speed=1.25)
  data=LIVE_BUILDERS[c['id']](c['params'])[0];chk=live_checks(c['id'],c['params']);end=chk['end'];probe=chk['probe']
  rec['sha256']=hashlib.sha256(frag.encode()).hexdigest();rec['bytes']=len(frag.encode())
  (OUT/c['id']).mkdir(parents=True,exist_ok=True);(OUT/c['id']/'macro.html').write_text(frag,encoding='utf8');(OUT/c['id']/'preview.html').write_text(document(frag,c['title']),encoding='utf8')
  ctx=browser.new_context(viewport={'width':800,'height':1000});page=ctx.new_page();errors=[];reqs=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('request',lambda r:reqs.append(r.url))
  page.set_content(wrap(frag,715));page.wait_for_timeout(700)
  t1=float(page.get_attribute('[data-ca-prefix]','data-ca-t'));page.wait_for_timeout(400);t2=float(page.get_attribute('[data-ca-prefix]','data-ca-t'))
  assert 0<t1<t2<end,(t1,t2);rec['checks']['autoplay_from_start_and_advances']=[t1,t2]
  root=page.locator('[data-ca-prefix]')
  # Height budget and per-time checks at two widths.
  samples=chk['samples']
  for width in (715,360):
   page.set_viewport_size({'width':800 if width==715 else 360,'height':1000});page.set_content(wrap(frag,715 if width==715 else None));page.wait_for_timeout(250)
   h=root.bounding_box()['height'];assert h<=BUDGET[width],(width,h);rec['checks'][f'height_{width}']=round(h)
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),width
   for t in samples:
    seek(page,prefix,t);page.wait_for_timeout(40);o=root.evaluate(OVERLAP_JS);assert not o['bad'] and not o['out'],(width,t,o)
    st=live_state(page,prefix);want=probe(t)
    assert model_matches(st,want['state']),(t,st,want)
    nums=stats_numbers(page,prefix);assert nums[:len(want['stats'])]==want['stats'],(t,nums,want)
    want=[x for x in data['captions'] if t>=x[0]-1e-9][-1][2];assert want in root.locator('[data-ca-caption]').inner_text(),(t,want)
    root.screenshot(path=str(SHOTS/f"{c['id']}-{width}-{t:.2f}.png"))
   rec['checks'][f'no_text_overlap_or_clip_{width}']=len(samples);rec['checks'][f'state_matches_python_model_{width}']=len(samples)
   bad=root.evaluate(CONTRAST_JS);assert not bad,('low contrast text',width,bad[:5]);rec['checks'][f'text_contrast_aa_{width}']=True
   mf=page.evaluate(MINFONT_JS,'svg[data-ca-live]');assert mf>=9,(width,mf);rec['checks'][f'min_text_px_{width}']=round(mf,1)
  rec['checks']['captions_match_model_events']=True
  # Annotations must not appear before the event they describe.
  page.set_viewport_size({'width':800,'height':1000});page.set_content(wrap(frag,715));page.wait_for_timeout(200)
  for label,at in chk['annotations']:
   seek(page,prefix,at-0.06);assert label not in root.locator('svg[data-ca-live]').inner_html(),('future leak',label)
   seek(page,prefix,at+0.06);assert label in root.locator('svg[data-ca-live]').inner_html(),('missing',label)
  rec['checks']['no_future_annotation_leak']=True
  # Controls: end / restart / pause, keyboard.
  root.locator('[data-a="end"]').click();assert abs(live_state(page,prefix)['T']-end)<1e-6
  root.locator('[data-a="restart"]').click();page.wait_for_timeout(300);s1=live_state(page,prefix);assert s1['playing'] and 0<s1['T']<end
  root.locator('[data-a="play"]').click();a=live_state(page,prefix)['T'];page.wait_for_timeout(250);assert live_state(page,prefix)['T']==a
  root.locator('[data-a="play"]').focus();page.keyboard.press('Enter');page.wait_for_timeout(250);assert live_state(page,prefix)['T']>a
  rec['checks']['controls_end_restart_pause_keyboard']=True
  # Resize keeps the model clock.
  ra=chk['resize_at'];seek(page,prefix,ra);before=page.locator('svg[data-ca-live]').get_attribute('viewBox').split()[2]
  page.set_viewport_size({'width':420,'height':1000});page.evaluate('document.querySelector("[data-ca-prefix]").parentElement.style.width="400px"');page.wait_for_timeout(250)
  after=page.locator('svg[data-ca-live]').get_attribute('viewBox').split()[2]
  assert abs(live_state(page,prefix)['T']-ra)<1e-6;assert after!=before and float(after)<=400,(before,after)
  rec['checks']['resize_relayout_keeps_clock']=True
  # Print: final scene, controls hidden.
  page.set_viewport_size({'width':800,'height':1000});page.set_content(wrap(frag,715));page.wait_for_timeout(500)
  page.pdf(path=str(OUT/c['id']/'print.pdf'));assert abs(live_state(page,prefix)['T']-end)<1e-6
  page.emulate_media(media='print');assert root.locator('[data-ca-controls]').is_hidden();page.emulate_media(media='screen')
  rec['checks']['print_final_scene_controls_hidden']=True
  # Two instances run independently.
  b,_=build_case(c,'ca-live-c',speed=1.25);page.set_content(wrap(frag+b,715));page.wait_for_timeout(500)
  page.locator('[data-ca-prefix="ca-live-b"] [data-a="play"]').click();x=live_state(page,'ca-live-b')['T'];y=live_state(page,'ca-live-c')['T'];page.wait_for_timeout(300)
  assert live_state(page,'ca-live-b')['T']==x and live_state(page,'ca-live-c')['T']>y;rec['checks']['independent_instances']=True
  assert not errors,errors;assert not [u for u in reqs if u.startswith(('http:','https:'))];rec['checks']['no_errors_no_external_requests']=True
  ctx.close()
  # Reduced motion: final scene, no autoplay.
  ctx=browser.new_context(viewport={'width':800,'height':1000},reduced_motion='reduce');page=ctx.new_page();page.set_content(wrap(frag,715));page.wait_for_timeout(600)
  st=live_state(page,prefix);assert abs(st['T']-end)<1e-6 and not st['playing'];rec['checks']['reduced_motion_final_no_autoplay']=True;ctx.close()
  # No JavaScript (export-like): static final scene from the same draw code, controls hidden.
  ctx=browser.new_context(viewport={'width':800,'height':1000},java_script_enabled=False);page=ctx.new_page();page.set_content(wrap(frag,715))
  assert page.locator('svg[data-ca-static] text').count()>=8;assert page.locator('[data-ca-controls]').evaluate('e=>getComputedStyle(e).visibility')=='hidden'
  assert data['captions'][-1][2] in page.locator('[data-ca-caption]').inner_text()
  page.locator('[data-ca-prefix]').screenshot(path=str(SHOTS/f"{c['id']}-nojs.png"));rec['checks']['nojs_static_final_scene']=True;ctx.close()
  # No JavaScript on a phone: the 360 px static scene is shown instead of a shrunken wide one.
  ctx=browser.new_context(viewport={'width':360,'height':900},java_script_enabled=False);page=ctx.new_page();page.set_content(wrap(frag,None))
  assert page.locator('svg[data-ca-narrow]').is_visible() and page.locator('svg[data-ca-live]').is_hidden()
  mf=page.evaluate(MINFONT_JS,'svg[data-ca-narrow]');assert mf>=9,('nojs narrow text too small',mf)
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
  page.locator('[data-ca-prefix]').screenshot(path=str(SHOTS/f"{c['id']}-nojs-360.png"));rec['checks']['nojs_phone_static_scene_min_text_px']=round(mf,1);ctx.close()
  # Gallery mounts and runs the exact macro.
  gallery=ROOT/'dist/monitoring-suite/gallery.html'
  if gallery.exists():
   ctx=browser.new_context(viewport={'width':1450,'height':1050});gp=ctx.new_page();ge=[];gp.on('pageerror',lambda e:ge.append(str(e)))
   gp.set_content(gallery.read_text(encoding='utf8'));gp.wait_for_timeout(150)
   gp.evaluate(f"location.hash='{c['id']}'");gp.set_content(gallery.read_text(encoding='utf8'));gp.wait_for_timeout(100)
   ids=[x['id'] for x in json.loads((ROOT/'dist/monitoring-suite/manifest.json').read_text())['cases']]
   gp.locator('#lab-list button').nth(ids.index(c['id'])).click();gp.wait_for_timeout(900)
   assert gp.locator('#lab-preview [data-ca-live-bound]').count()==1;t=float(gp.get_attribute('#lab-preview [data-ca-prefix]','data-ca-t'));assert 0<t<end,t
   assert not ge,ge;rec['checks']['gallery_executes_live_macro']=True;ctx.close()
  report['cases'].append(rec);print('PASS',c['id'],json.dumps(rec['checks'],ensure_ascii=False))
 browser.close()
report['result']='PASS';report['test_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(OUT/'live-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
