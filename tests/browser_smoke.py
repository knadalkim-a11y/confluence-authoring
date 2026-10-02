#!/usr/bin/env python3
"""Browser verification, separate from Python unit tests. Requires Playwright + Chromium.

Uses set_content on locally generated HTML; does not navigate to external websites.
JavaScript is disabled in macro contexts; evaluate is used only as test instrumentation.
"""
import argparse
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from motion import ROOT,render,document
from build_gallery import build
from playwright.sync_api import sync_playwright

SNAP='''() => Array.from(document.querySelectorAll('.ca-anim')).map(el=>{const s=getComputedStyle(el);return [s.opacity,s.transform,s.backgroundColor,s.borderColor,s.strokeDashoffset]})'''
SEEK='''fraction=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=a.effect.getTiming().duration*fraction})'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',default='/usr/bin/chromium')
    parser.add_argument('--output',type=Path,default=ROOT/'tests/browser-report.json')
    parser.add_argument('--screenshots',type=Path,default=ROOT/'dist/screenshots')
    args=parser.parse_args()
    build(ROOT/'dist')
    examples=json.loads((ROOT/'examples/motion-inputs.json').read_text(encoding='utf-8'))
    args.screenshots.mkdir(parents=True,exist_ok=True)
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'mode':'local generated content','javascript_in_macro_context':False,'confluence':'not-verified','patterns':{},'gallery':{},'network_requests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.browser,headless=True,args=['--no-sandbox'])
        report['browser']=browser.version
        context=browser.new_context(java_script_enabled=False,viewport={'width':1060,'height':900})
        context.on('request',lambda request:report['network_requests'].append(request.url))
        page=context.new_page()
        for i,(pattern,data) in enumerate(examples.items()):
            page.emulate_media(media='screen',reduced_motion='no-preference')
            page.set_viewport_size({'width':1060,'height':900})
            page.set_content(document(render(pattern,data,'ca-browser-'+str(i))))
            page.wait_for_timeout(70)
            first=page.evaluate('()=>document.getAnimations().map(a=>a.currentTime)')
            page.wait_for_timeout(100)
            second=page.evaluate('()=>document.getAnimations().map(a=>a.currentTime)')
            assert first and any(b>a for a,b in zip(first,second)),pattern+' clock does not advance'
            page.evaluate(SEEK,.10);s1=page.evaluate(SNAP)
            page.evaluate(SEEK,.78);s2=page.evaluate(SNAP)
            assert s1!=s2,pattern+' no visual state difference'
            # Reset after Web Animations instrumentation so CSS controls are tested without API play-state overrides.
            page.set_content(document(render(pattern,data,'ca-browser-'+str(i))))
            page.wait_for_timeout(80)
            page.locator('.ca-pause-label').click()
            page.wait_for_timeout(60)
            assert page.evaluate("()=>document.getAnimations().every(a=>a.playState==='paused')")
            paused=page.evaluate(SNAP);page.wait_for_timeout(70)
            assert paused==page.evaluate(SNAP),pattern+' pause moves'
            page.locator('.ca-replay-label').click()
            assert page.evaluate('()=>document.getAnimations().every(a=>a.currentTime<100)')
            page.locator('.ca-pause-label').click();page.wait_for_timeout(100)
            assert page.evaluate("()=>document.getAnimations().some(a=>a.playState==='running'&&a.currentTime>0)")
            page.evaluate(SEEK,.99);final=page.evaluate(SNAP)
            page.set_content(document(render(pattern,data,'ca-browser-'+str(i))))
            page.locator('.ca-still-label').click()
            assert not page.evaluate('()=>document.getAnimations().length')
            assert final==page.evaluate(SNAP),pattern+' static state differs from end'
            assert page.locator('.ca-caption').is_visible()
            page.screenshot(path=str(args.screenshots/(pattern+'-wide.png')),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1'),pattern+' mobile overflow'
            page.screenshot(path=str(args.screenshots/(pattern+'-narrow.png')),full_page=True)
            page.emulate_media(reduced_motion='reduce')
            assert page.locator('.ca-tools').is_hidden()
            assert not page.evaluate('()=>document.getAnimations().length')
            assert page.locator('.ca-caption').is_visible()
            page.emulate_media(media='print',reduced_motion='no-preference')
            assert page.locator('.ca-tools').is_hidden()
            assert page.locator('.ca-caption').is_visible()
            report['patterns'][pattern]={'clock':'pass','state_transitions':'pass','pause_resume':'pass','replay':'pass','static_equals_final':'pass','width_390':'pass','reduced_motion':'pass','print':'pass'}
        page.emulate_media(media='screen',reduced_motion='no-preference')
        a=render('line-reveal',examples['line-reveal'],'ca-multi-a')
        b=render('line-reveal',examples['line-reveal'],'ca-multi-b')
        page.set_content(document(a+b));page.locator('.ca-multi-a .ca-pause-label').click()
        assert page.locator('.ca-multi-a .ca-pause').is_checked()
        assert not page.locator('.ca-multi-b .ca-pause').is_checked()
        assert page.evaluate("()=>document.querySelector('.ca-multi-b').getAnimations({subtree:true}).every(a=>a.playState==='running')")
        report['multi_instance_controls']='pass'
        page.set_content(document(a));page.keyboard.press('Tab')
        assert page.evaluate("()=>document.activeElement.id==='ca-multi-a-pause'")
        page.keyboard.press('Space')
        assert page.locator('.ca-pause').is_checked()
        report['keyboard']='pass'
        gcontext=browser.new_context(viewport={'width':1380,'height':1000})
        gcontext.on('request',lambda request:report['network_requests'].append(request.url))
        gallery=gcontext.new_page();errors=[]
        gallery.on('pageerror',lambda error:errors.append(str(error)))
        gallery.set_content((ROOT/'dist/gallery.html').read_text(encoding='utf-8'))
        assert gallery.locator('#items button').count()==13
        for key in examples:
            gallery.locator(f'#items button[data-id="{key}"]').click()
            assert gallery.locator('#preview [data-ca-pattern]').count()==1
            assert gallery.locator('#preview [data-ca-pattern]').get_attribute('data-ca-pattern')==key
        gallery.locator('#search').fill('병렬')
        assert gallery.locator('#items button').count()==1
        gallery.locator('#search').fill('없는패턴zxy')
        assert gallery.locator('#items button').count()==0
        assert gallery.locator('.empty').is_visible()
        gallery.locator('#search').fill('')
        gallery.locator('#category').select_option('process')
        assert gallery.locator('#items button').count()==5
        gallery.locator('#category').select_option('all')
        gallery.locator('#items button[data-id="parallel-flow"]').click()
        gallery.get_by_role('button',name='매크로 코드 보기',exact=True).click()
        assert gallery.locator('#code').is_visible()
        assert '<script' not in gallery.locator('#code').input_value()
        gallery.get_by_role('button',name='매크로 코드 보기',exact=True).click()
        gallery.locator('.ca-still-label').click()
        gallery.screenshot(path=str(args.screenshots/'gallery-wide.png'),full_page=True)
        gallery.set_viewport_size({'width':390,'height':844})
        assert gallery.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1')
        gallery.screenshot(path=str(args.screenshots/'gallery-narrow.png'),full_page=True)
        assert not errors,errors
        report['gallery']={'all_13_selectable':'pass','search':'pass','category_filter':'pass','empty_state':'pass','source_code_view':'pass','only_one_live_preview':'pass','width_390':'pass','script_errors':errors}
        assert not report['network_requests'],report['network_requests']
        browser.close()
    report['result']='pass'
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
