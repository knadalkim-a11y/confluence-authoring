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
from monitoring_cases import build_case,pool_model,pool_state,LIVE_BUILDERS
from reference_scene import document
ap=argparse.ArgumentParser();ap.add_argument('--browser');ap.add_argument('--output',type=Path,default=ROOT/'dist/live')
opt=ap.parse_args();OUT=opt.output;SHOTS=OUT/'screenshots';SHOTS.mkdir(parents=True,exist_ok=True)
CASES=[c for c in json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases'] if c.get('runtime')=='live']
BUDGET={715:520,360:600}
report={'confluence_verified':False,'tested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'cases':[]}

OVERLAP_JS="""(root)=>{const t=[...root.querySelectorAll('svg[data-ca-live] text')].map(e=>{const r=e.getBoundingClientRect();return {s:e.textContent,x:r.left,y:r.top,r:r.right,b:r.bottom}}).filter(a=>a.r>a.x);
 const bad=[];for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++){const a=t[i],b=t[j],w=Math.min(a.r,b.r)-Math.max(a.x,b.x),h=Math.min(a.b,b.b)-Math.max(a.y,b.y);if(w>1.5&&h>1.5)bad.push([a.s,b.s,Math.round(w),Math.round(h)])}
 const box=root.getBoundingClientRect();const out=t.filter(a=>a.x<box.left-1||a.r>box.right+1).map(a=>a.s);return {bad,out}}"""
def wrap(fragment,width):
 return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0">'+(
  f'<div style="width:{width}px;margin:0 auto">' if width else '<div>')+fragment+'</div></body></html>'
def seek(page,prefix,t):page.evaluate('([p,t])=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.seek(t)',[prefix,t])
def live_state(page,prefix):return page.evaluate('(p)=>document.querySelector(`[data-ca-prefix="${p}"]`).__caLive.state()',prefix)
def stats_numbers(page,prefix):return page.locator(f'[data-ca-prefix="{prefix}"] [data-ca-stats] b').all_inner_texts()

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=opt.browser,headless=True,args=['--no-sandbox'])
 report['browser']=browser.version
 for c in CASES:
  rec={'id':c['id'],'checks':{}};prefix='ca-live-b';frag,model=build_case(c,prefix,speed=1.25)
  data=LIVE_BUILDERS[c['id']](c['params'])[0];end=data['params']['horizon'];jobs=pool_model(c['params'])
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
  samples=[0.5,data['params']['slow_start']+0.6,(data['events']['t_queue'] or 5)+0.5,data['events']['t_queue_max'] or 9,data['params']['recovery']+1.5,end]
  for width in (715,360):
   page.set_viewport_size({'width':800 if width==715 else 360,'height':1000});page.set_content(wrap(frag,715 if width==715 else None));page.wait_for_timeout(250)
   h=root.bounding_box()['height'];assert h<=BUDGET[width],(width,h);rec['checks'][f'height_{width}']=round(h)
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),width
   for t in samples:
    seek(page,prefix,t);page.wait_for_timeout(40);o=root.evaluate(OVERLAP_JS);assert not o['bad'] and not o['out'],(width,t,o)
    st=live_state(page,prefix);ps=pool_state(jobs,t)
    assert st['used']==ps['active'] and st['queued']==ps['queued'],(t,st,ps)
    nums=stats_numbers(page,prefix);assert nums[0]==str(ps['active']) and nums[1]==str(ps['queued']),(t,nums,ps)
    want=[x for x in data['captions'] if t>=x[0]-1e-9][-1][2];assert want in root.locator('[data-ca-caption]').inner_text(),(t,want)
    root.screenshot(path=str(SHOTS/f"{c['id']}-{width}-{t:.2f}.png"))
   rec['checks'][f'no_text_overlap_or_clip_{width}']=len(samples);rec['checks'][f'state_matches_python_model_{width}']=len(samples)
  rec['checks']['captions_match_model_events']=True
  # Annotations must not appear before the event they describe.
  page.set_viewport_size({'width':800,'height':1000});page.set_content(wrap(frag,715));page.wait_for_timeout(200)
  ev=data['events'];maxj=jobs[ev['max_job']]
  for label,at in [('최대 대기',ev['t_queue_max']),('최대 '+f"{maxj['end']-maxj['arrive']:.1f}초",maxj['end'])]:
   if at is None:continue
   seek(page,prefix,at-0.06);assert label not in root.locator('svg').inner_html(),('future leak',label)
   seek(page,prefix,at+0.06);assert label in root.locator('svg').inner_html(),('missing',label)
  rec['checks']['no_future_annotation_leak']=True
  # Controls: end / restart / pause, keyboard.
  root.locator('[data-a="end"]').click();assert abs(live_state(page,prefix)['T']-end)<1e-6
  root.locator('[data-a="restart"]').click();page.wait_for_timeout(300);s1=live_state(page,prefix);assert s1['playing'] and 0<s1['T']<end
  root.locator('[data-a="play"]').click();a=live_state(page,prefix)['T'];page.wait_for_timeout(250);assert live_state(page,prefix)['T']==a
  root.locator('[data-a="play"]').focus();page.keyboard.press('Enter');page.wait_for_timeout(250);assert live_state(page,prefix)['T']>a
  rec['checks']['controls_end_restart_pause_keyboard']=True
  # Resize keeps the model clock.
  seek(page,prefix,6.0);page.set_viewport_size({'width':420,'height':1000});page.wait_for_timeout(200)
  assert abs(live_state(page,prefix)['T']-6.0)<1e-6;assert page.locator('svg[data-ca-live]').get_attribute('viewBox').split()[2]!='715'
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
  assert page.locator('svg[data-ca-static] text').count()>20;assert page.locator('[data-ca-controls]').evaluate('e=>getComputedStyle(e).visibility')=='hidden'
  assert data['captions'][-1][2] in page.locator('[data-ca-caption]').inner_text()
  page.locator('[data-ca-prefix]').screenshot(path=str(SHOTS/f"{c['id']}-nojs.png"));rec['checks']['nojs_static_final_scene']=True;ctx.close()
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
