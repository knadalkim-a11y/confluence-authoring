"""Rendered rail/particle coincidence and readability for the three layout revisions."""
from pathlib import Path
import hashlib,json,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/monitoring-suite'
SHOTS=OUT/'layout-screens';SHOTS.mkdir(exist_ok=True)
CASES=('cluster-cascade','event-loop','pipeline-bottleneck')
report={'result':'RUNNING','cases':[],'original_live_ab':False,'confluence_rendering':False}

def seek(page,t,speed=1.25):
    page.evaluate('t=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=t})',18000/speed*(.06+.8*t))
    page.wait_for_timeout(25)

TRACK_CHECK=r'''svg=>{
 const vis=e=>{for(let n=e;n&&n!==svg.parentElement;n=n.parentElement){const c=getComputedStyle(n);if(c.visibility==='hidden'||c.display==='none'||Number(c.opacity)<.9)return false}return true};
 let maximum=0,count=0;
 for(const token of svg.querySelectorAll('[data-motion-edge]')){
  if(!vis(token))continue;
  const style=getComputedStyle(token), path=document.createElementNS('http://www.w3.org/2000/svg','path');
  path.setAttribute('d',token.dataset.motionPath);
  if(!style.offsetPath.startsWith('path('))throw Error('Missing motion path');
  const distance=parseFloat(style.offsetDistance)/100;
  const point=path.getPointAtLength(path.getTotalLength()*distance);
  const screen=new DOMPoint(point.x,point.y).matrixTransform(svg.getScreenCTM());
  const box=token.getBoundingClientRect(),error=Math.hypot(screen.x-(box.x+box.width/2),screen.y-(box.y+box.height/2));
  if(error>1)throw Error(`${token.dataset.motionEdge}: rail/path error ${error.toFixed(3)}px`);
  maximum=Math.max(maximum,error);count++;
 }
 const texts=[...svg.querySelectorAll('text')].filter(vis).map(e=>({value:e.textContent,b:e.getBoundingClientRect()}));
 const overlaps=[];
 for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){
  const a=texts[i].b,b=texts[j].b,dx=Math.min(a.right,b.right)-Math.max(a.left,b.left),dy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
  if(dx>1&&dy>1)overlaps.push([texts[i].value,texts[j].value,dx,dy]);
 }
 if(overlaps.length)throw Error('Overlapping visible labels: '+JSON.stringify(overlaps));
 return {count,max_deviation_px:maximum,visible_labels:texts.length};
}'''
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    report['browser']=browser.version
    pg=browser.new_page(java_script_enabled=False,viewport={'width':1160,'height':1040})
    requests=[];pg.on('request',lambda r:requests.append(r.url))
    for cid in CASES:
        record={'id':cid,'checks':[],'max_path_deviation_px':0,'visible_tokens_checked':0}
        html=(OUT/cid/'preview.html').read_text()
        for width in (1160,390,320):
            pg.set_viewport_size({'width':width,'height':1040});pg.set_content(html)
            svg=pg.locator('.mechanism-wide' if width==1160 else '.mechanism-narrow')
            assert svg.is_visible()
            for t in (.14,.24,.36,.46,.53,.66,.74,.85,.95,1):
                seek(pg,t);result=svg.evaluate(TRACK_CHECK)
                record['visible_tokens_checked']+=result['count'];record['max_path_deviation_px']=max(record['max_path_deviation_px'],result['max_deviation_px'])
                assert not pg.evaluate('document.documentElement.scrollWidth>innerWidth')
            record['checks'].append(f'{width}px: actual token/rail coincidence, no label overlap, no page overflow')
            for t,label in ((.16,'normal'),(.53,'middle'),(1,'final')):
                seek(pg,t);pg.screenshot(path=str(SHOTS/f'{cid}-{width}-{label}.png'),full_page=True)
        assert record['visible_tokens_checked']>5
        # Resize while held in the middle: no timing reset or model fork.
        pg.set_viewport_size({'width':1160,'height':1040});pg.set_content(html);seek(pg,.53)
        before=pg.evaluate('document.getAnimations().map(a=>a.currentTime)')
        pg.set_viewport_size({'width':390,'height':1040});pg.wait_for_timeout(35)
        after=pg.evaluate('document.getAnimations().map(a=>a.currentTime)');assert before==after
        record['checks'].append('responsive switch preserves every animation clock')
        record['sha256']=hashlib.sha256((OUT/cid/'macro.html').read_bytes()).hexdigest()
        report['cases'].append(record);print('PASS geometry',cid,flush=True)
    assert not [r for r in requests if r.startswith(('http:','https:'))]
    gp=browser.new_page(java_script_enabled=True,accept_downloads=True,viewport={'width':1420,'height':1000});errors=[]
    gp.on('pageerror',lambda e:errors.append(str(e)))
    gp.set_content((OUT/'gallery.html').read_text())
    for cid in CASES:
        gp.locator('#lab-search').fill(cid);gp.locator('#lab-list button').click()
        assert gp.locator('#lab-baseline').is_enabled()
        for old in (False,True):
            if old:gp.locator('#lab-baseline').click()
            for speed in ('1','1.25','1.5'):
                gp.locator('#lab-speed').select_option(speed);gp.wait_for_timeout(35)
                assert gp.locator('#lab-preview [data-ca-pattern]').count()==1
                dur=gp.locator('#lab-preview .ca-anim').first.evaluate('e=>getComputedStyle(e).animationDuration')
                assert abs(float(dur[:-1])-18/float(speed))<.001
                gp.locator('#lab-code-toggle').click();code=gp.locator('#lab-code').input_value()
                with gp.expect_download() as info:gp.locator('#lab-download').click()
                assert Path(info.value.path()).read_text()==code
        report.setdefault('gallery_checks',[]).append(cid+': previous v0.3.1/current at all 3 speeds; exact macro export')
    gp.locator('#lab-search').fill('');gp.locator('#lab-list button').nth(0).click();assert gp.locator('#lab-baseline').is_disabled()
    assert not errors
    gp.locator('#lab-search').fill('cluster-cascade');gp.locator('#lab-list button').click();seek(gp,.53)
    gp.screenshot(path=str(SHOTS/'gallery-wide.png'),full_page=True)
    browser.close()
report.update(result='PASS',macro_external_requests=[],test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(OUT/'layout-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
