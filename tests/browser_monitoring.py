"""Actual local browser regression. Does not fetch the original website.

Macro JavaScript is disabled. Playwright evaluations are test instrumentation,
not code shipped with the macro. Run after build_monitoring_suite.py.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
import json,hashlib,sys,math,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/monitoring-suite';SHOTS=OUT/'screenshots';SHOTS.mkdir(exist_ok=True)
import argparse
args=argparse.ArgumentParser()
args.add_argument('--start',type=int,default=0)
args.add_argument('--count',type=int,default=19)
args.add_argument('--extra-only',action='store_true')
args.add_argument('--skip-extra',action='store_true')
options=args.parse_args()
manifest=json.loads((OUT/'manifest.json').read_text());cases=manifest['cases'];report={'original_live_browser_verified':False,'confluence_verified':False,'macro_javascript':False,'cases':[],'checks':{},'tested_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}

def state(page):
 return page.locator('.ca-stage .ca-anim').evaluate_all('(els)=>els.filter(e=>!e.closest(".mr-progress")).map(e=>{let s=getComputedStyle(e);return [s.transform,s.opacity,s.fill,(e.namespaceURI==="http://www.w3.org/2000/svg"&&e.tagName.toLowerCase()==="rect")?s.width:null,s.backgroundColor,s.borderColor]})')
def clocks(page):return page.evaluate('document.getAnimations().map(a=>a.currentTime)')
def seek(page,t):page.evaluate('(t)=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=t})',t*1000);page.wait_for_timeout(30)
def morph(page):
 return page.locator('svg .ca-anim').evaluate_all('(els)=>els.map(e=>{let s=getComputedStyle(e);return [s.transform,s.opacity,s.fill,s.width]})')
with sync_playwright() as p:
 exe='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None  # else Playwright's bundled Chromium
 browser=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
 report['browser']=browser.version;context=browser.new_context(viewport={'width':1180,'height':980},java_script_enabled=False);page=context.new_page();requests=[];errors=[]
 page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
 # Live-runtime cases need JavaScript; tests/browser_live.py covers them.
 for c in ([] if options.extra_only else [x for x in cases[options.start:options.start+options.count] if x.get('runtime')!='live']):
  record={'id':c['id'],'sha256':c['sha256'],'checks':{}}
  content=(OUT/c['id']/'preview.html').read_text();page.set_content(content);page.wait_for_timeout(80)
  before=clocks(page);page.wait_for_timeout(90);after=clocks(page);assert len(before)>0 and max(after)>max(before)
  record['checks']['clock_advances']=True;record['animations']=len(after)
  # The actual visual tracks, excluding the progress bar, must change continuously somewhere.
  differences=[]
  for t in [2.0,3.3,5.1,7.8,10.4,12.2]:
   seek(page,t);a=morph(page);seek(page,t+.05);b=morph(page);differences.append(a!=b)
  assert any(differences),c['id'];record['checks']['visual_intermediate_state_changes']=sum(differences)
  for t,label in [(2,'start'),(9,'middle'),(18.1,'final')]:
   seek(page,t);page.screenshot(path=str(SHOTS/(c['id']+'-'+label+'.png')),full_page=True)
  final=state(page);page.locator('.ca-still-label').click();page.wait_for_timeout(30)
  assert final==state(page),(c['id'],'static final mismatch');record['checks']['static_equals_final']=True
  for width in [390,320]:
   page.set_viewport_size({'width':width,'height':900});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(c['id'],width,'overflow')
  page.set_viewport_size({'width':390,'height':900});page.screenshot(path=str(SHOTS/(c['id']+'-narrow.png')),full_page=True)
  record['checks']['320_and_390_no_horizontal_overflow']=True
  page.set_viewport_size({'width':1180,'height':980});page.locator('[data-ca-prefix]').evaluate('(e)=>e.style.maxWidth="360px"')
  assert page.locator('[data-ca-prefix]').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
  record['checks']['360px_container_on_wide_view']=True
  page.set_content(content);page.wait_for_timeout(100)
  page.locator('.ca-pause-label').click();page.wait_for_timeout(30);a=clocks(page);page.wait_for_timeout(90);b=clocks(page)
  assert all(abs(x-y)<2 for x,y in zip(a,b))
  page.locator('.ca-pause-label').click();page.wait_for_timeout(90);assert max(clocks(page))>max(b)
  page.locator('.ca-replay-label').click();page.wait_for_timeout(20);assert max(clocks(page))<180
  record['checks']['css_pause_resume_replay']=True
  seek(page,18.1);final=state(page)
  page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(30);assert final==state(page),(c['id'],'fallback state mismatch',[(x,y) for x,y in zip(final,state(page)) if x!=y][:3]);assert page.locator('.ca-tools').is_hidden()
  record['checks']['reduced_motion_equals_final']=True
  page.emulate_media(media='print',reduced_motion='no-preference');page.wait_for_timeout(30);assert final==state(page),(c['id'],'fallback state mismatch',[(x,y) for x,y in zip(final,state(page)) if x!=y][:3]);assert page.locator('.ca-tools').is_hidden()
  record['checks']['print_equals_final']=True
  page.emulate_media(media='screen',reduced_motion='no-preference');report['cases'].append(record);print('PASS',c['id'],flush=True)
 if not options.skip_extra:
  # Independent instances + keyboard operation.
  css_index,css_case=next((i,x['id']) for i,x in enumerate(cases) if x['id']=='memory-leak');own=f'ca-monitor-{css_index:02d}'
  text=(OUT/css_case/'macro.html').read_text();second=text.replace(own,'ca-independent')
  page.set_content('<html><body>'+text+second+'</body></html>');page.wait_for_timeout(80)
  page.locator('.ca-pause-label').first.click();page.wait_for_timeout(50);a=page.evaluate('document.getAnimations().map(a=>[a.effect.target.closest("section").dataset.caPrefix,a.currentTime])');page.wait_for_timeout(100);b=page.evaluate('document.getAnimations().map(a=>[a.effect.target.closest("section").dataset.caPrefix,a.currentTime])')
  assert all(abs(x[1]-y[1])<2 for x,y in zip(a,b) if x[0]==own);assert any(y[1]>x[1] for x,y in zip(a,b) if x[0]=='ca-independent')
  report['checks']['independent_instances']=True
  page.set_content((OUT/'traffic-patterns'/'preview.html').read_text());page.keyboard.press('Tab');assert page.locator('.ca-pause').evaluate('(e)=>e===document.activeElement');page.keyboard.press('Space');assert page.locator('.ca-pause').is_checked();assert page.locator('.ca-pause-label').evaluate('(e)=>getComputedStyle(e).outlineStyle')!='none'
  report['checks']['keyboard_visible_focus']=True
  # Event-loop rotation holds while global time proceeds.
  page.set_content((OUT/'event-loop'/'preview.html').read_text());seek(page,14.4*(.06+.8*.4));a=page.locator('[data-event-rotor]').first.evaluate('(e)=>getComputedStyle(e).transform');seek(page,14.4*(.06+.8*.55));b=page.locator('[data-event-rotor]').first.evaluate('(e)=>getComputedStyle(e).transform');assert a==b,(a,b)
  report['checks']['event_loop_actual_rotation_holds']=True
  # Exact worker state at a model time, not merely an animation presence test.
  # thread-pool now uses the live runtime; its exact model-state checks are in tests/browser_live.py.
  report['checks']['macro_external_requests']=[u for u in requests if u.startswith(('http:','https:'))];assert not report['checks']['macro_external_requests'];assert not errors
  # Gallery JavaScript is used only for UI and mounts the exact pre-rendered fragment.
  gc=browser.new_context(viewport={'width':1450,'height':1050},java_script_enabled=True);gp=gc.new_page();gr=[];ge=[];gp.on('request',lambda r:gr.append(r.url));gp.on('pageerror',lambda e:ge.append(str(e)))
  gp.set_content((OUT/'gallery.html').read_text());gp.wait_for_timeout(100)
  assert gp.locator('#lab-list button').count()==19
  for i,c in enumerate(cases):
   gp.locator('#lab-list button').nth(i).click();assert gp.locator('#lab-preview [data-ca-pattern]').count()==1;assert gp.locator('#lab-preview [data-ca-pattern]').get_attribute('data-ca-pattern')=='reference-'+c['id']
  gp.locator('#lab-filter').select_option('article');assert gp.locator('#lab-list button').count()==18
  gp.locator('#lab-search').fill('P99ZZNORESULT');assert gp.locator('#lab-list button').count()==0
  gp.locator('#lab-search').fill('분포');assert gp.locator('#lab-list button').count()>=1
  gp.locator('#lab-search').fill('');gp.locator('#lab-filter').select_option('all');gp.locator('#lab-list button').nth(1).click();gp.locator('#lab-code-toggle').click();assert gp.locator('#lab-code').input_value()==(OUT/'percentile-comparison'/'macro.html').read_text()
  gp.locator('#lab-input-toggle').click();assert json.loads(gp.locator('#lab-code').input_value())['id']=='percentile-comparison'
  gp.locator('#lab-list button').nth(10).click();seek(gp,10)
  gp.screenshot(path=str(SHOTS/'gallery-wide.png'),full_page=True);gp.set_viewport_size({'width':390,'height':950});assert not gp.evaluate('document.documentElement.scrollWidth>innerWidth');gp.screenshot(path=str(SHOTS/'gallery-narrow.png'),full_page=True)
  assert not ge;assert not [u for u in gr if u.startswith(('http:','https:'))]
  report['checks']['gallery_all_cases_filter_search_exact_code_and_single_preview']=True
  report['checks']['gallery_external_requests']=gr;report['checks']['gallery_errors']=ge
 browser.close()
report['result']='PASS';report['case_count']=len(report['cases'])
report['test_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report_name=('browser-extra.json' if options.extra_only else f'browser-cases-{options.start}-{options.count}.json' if options.skip_extra else 'browser-report.json')
(OUT/report_name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'result':report['result'],'cases':len(report['cases']),'checks':report['checks']},ensure_ascii=False,indent=2))
for offset in range(0,len(cases),5):
 group=cases[offset:offset+5];sheet=Image.new('RGB',(1500,len(group)*365),'#eef2f7');draw=ImageDraw.Draw(sheet)
 for i,c in enumerate(group):
  for j,suffix in enumerate(['final','middle','narrow']):
   shot=SHOTS/(c['id']+'-'+suffix+'.png')
   if not shot.exists():continue  # Later shards may not have rendered this case yet.
   img=Image.open(shot).convert('RGB');img.thumbnail((490,330));sheet.paste(img,(j*500,i*365+25));draw.text((j*500+5,i*365+5),c['id']+' / '+suffix,fill='#172b43')
 sheet.save(SHOTS/f'contact-{offset//5}.png')
