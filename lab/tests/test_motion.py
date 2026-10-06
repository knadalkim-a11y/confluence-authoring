"""Run: python -m unittest discover -s tests -v"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(1, str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'scripts'))   # the product scripts (model, live_scene, visual_spec)
from motion import ROOT, FIELDS, render, weighted_stats, queue_states
from validate_html_macro import validate
from build_gallery import build

EXAMPLES=json.loads((ROOT/'examples/motion-inputs.json').read_text(encoding='utf-8'))


class MotionTests(unittest.TestCase):
    def test_all_thirteen_render_and_lint(self):
        self.assertEqual(13,len(FIELDS))
        for pattern in FIELDS:
            with self.subTest(pattern=pattern):
                output=render(pattern,EXAMPLES[pattern],f'ca-test-{pattern}')
                self.assertEqual([],validate(output))
                self.assertNotIn('{{',output)
                self.assertIn('설명용 예시',output)
                self.assertIn('실제 소요 시간과 무관',output)

    def test_unique_prefix_and_multi_block_isolation(self):
        a=render('line-reveal',EXAMPLES['line-reveal'])
        b=render('line-reveal',EXAMPLES['line-reveal'])
        self.assertNotEqual(a,b)
        self.assertEqual([],validate(a+b))
        self.assertIn('Duplicate prefix',validate(a+a))
        self.assertIn('Duplicate ID',validate(a+a))
        self.assertIn('Duplicate keyframes',validate(a+a))

    def test_html_injection_is_text(self):
        d=copy.deepcopy(EXAMPLES['line-reveal'])
        d['title']='</h3><img src=x onerror=alert(1)> " &'
        output=render('line-reveal',d)
        self.assertEqual([],validate(output))
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;',output)
        self.assertNotIn('<img ',output)

    def test_bad_prefixes(self):
        for prefix in ['1bad','x','bad prefix','x"><script>','a'*42]:
            with self.subTest(prefix=prefix),self.assertRaises(ValueError):
                render('line-reveal',EXAMPLES['line-reveal'],prefix)

    def test_required_and_unknown_inputs(self):
        for key in ['title','description','caption','provenance','data_mode','series','unit','x_label','change_index']:
            d=copy.deepcopy(EXAMPLES['line-reveal']);del d[key]
            with self.subTest(key=key),self.assertRaises(ValueError):
                render('line-reveal',d)
        for value in [None, [], 123]:
            d=copy.deepcopy(EXAMPLES['line-reveal']);d['data_mode']=value
            with self.subTest(mode=value),self.assertRaises(ValueError):render('line-reveal',d)
        d=copy.deepcopy(EXAMPLES['line-reveal']);d['made_up']=1
        with self.assertRaises(ValueError):render('line-reveal',d)

    def test_invalid_numbers(self):
        for value in [-1,float('nan'),float('inf'),True,'100',None]:
            d=copy.deepcopy(EXAMPLES['line-reveal']);d['series'][1]=value
            with self.subTest(value=value),self.assertRaises(ValueError):render('line-reveal',d)

    def test_invalid_timing_and_repeat(self):
        for value in [0,31,True,'fast']:
            d=copy.deepcopy(EXAMPLES['line-reveal']);d['duration']=value
            with self.subTest(duration=value),self.assertRaises(ValueError):render('line-reveal',d)
        for value in [True,0,2,'1','forever']:
            d=copy.deepcopy(EXAMPLES['line-reveal']);d['repeat']=value
            with self.subTest(repeat=value),self.assertRaises(ValueError):render('line-reveal',d)

    def test_curve_and_summary_follow_data(self):
        d=copy.deepcopy(EXAMPLES['line-reveal'])
        old=render('line-reveal',d,'ca-chart')
        d['series']=[5,20,30,50,60,40,30,25,20,15,10]
        new=render('line-reveal',d,'ca-chart')
        self.assertNotEqual(re.search(r'points="([^"]+)"',old)[1],re.search(r'points="([^"]+)"',new)[1])
        self.assertIn('시작 5 → 마지막 10 ms',new)

    def test_percentile_is_derived_not_label_only(self):
        self.assertEqual((100,550),weighted_stats([50,550],[90,10]))
        self.assertEqual((100,150),weighted_stats([50,100,150],[20,60,20]))
        d=copy.deepcopy(EXAMPLES['distribution-percentile'])
        d.update(values=[50,100,150],counts=[20,60,20])
        output=render('distribution-percentile',d)
        self.assertIn('평균 100 ms · P95 150 ms',output)

    def test_distribution_validation(self):
        cases=[{'counts':[0,0]},{'counts':[10,-1]},{'counts':[1]},{'values':[50,50]},{'values':[50,float('inf')]},{'counts':[1.5,2]}]
        for patch in cases:
            d=copy.deepcopy(EXAMPLES['distribution-percentile']);d.update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):render('distribution-percentile',d)

    def test_queue_conservation(self):
        self.assertEqual([(3,0),(4,1),(4,5),(4,10),(4,15),(9,9)],queue_states([3,5,8,9,9,3],[4,4,4,4,4,9],0))
        d=EXAMPLES['queue-buildup']
        states=queue_states(d['arrivals'],d['capacity'],d['initial'])
        self.assertEqual(d['initial']+sum(d['arrivals']),sum(x for x,_ in states)+states[-1][1])
        self.assertIn('마지막 대기 9',render('queue-buildup',d))

    def test_no_crossing_and_recovery_order(self):
        d=copy.deepcopy(EXAMPLES['threshold-cross']);d['threshold']=99
        self.assertIn('임계치 초과 없음',render('threshold-cross',d))
        d=copy.deepcopy(EXAMPLES['recovery']);d['recovery_index']=1
        with self.assertRaises(ValueError):render('recovery',d)

    def test_bounded_retry(self):
        d=copy.deepcopy(EXAMPLES['retry-loop']);d['attempts'][0]['state']='done'
        with self.assertRaises(ValueError):render('retry-loop',d)
        d=copy.deepcopy(EXAMPLES['retry-loop']);d['attempts']*=3
        with self.assertRaises(ValueError):render('retry-loop',d)

    def test_approval_stays_waiting_in_static_output(self):
        result=render('approval-gate',EXAMPLES['approval-gate'],'ca-approval')
        self.assertIn('최종 상태: 대기',result)
        self.assertIn('검토 대기에서 멈춥니다',result)
        self.assertIn('background:#fff6e8',result)

    def test_unsupported_patterns_and_tokens(self):
        with self.assertRaises(ValueError):render('resource-exhaustion',{})
        d=copy.deepcopy(EXAMPLES['line-reveal']);d['title']='{{SECRET}}'
        with self.assertRaises(ValueError):render('line-reveal',d)

    def test_lint_hostile_fragments(self):
        good=render('line-reveal',EXAMPLES['line-reveal'],'ca-safe')
        for injection in ['<script>alert(1)</script>','<iframe srcdoc="bad"></iframe>','<svg onload="alert(1)"></svg>','<style>body{color:red}</style>','<style>@import "https://example.com";</style>','<style>.ca-safe{background:url(https://example.com/a.png)}</style>','<image href="data:image/svg+xml,bad"/>']:
            with self.subTest(injection=injection):self.assertTrue(validate(good+injection))

    def test_lint_allows_source_navigation_not_runtime_resource(self):
        good=render('line-reveal',EXAMPLES['line-reveal'],'ca-source')
        self.assertEqual([],validate(good+'<a href="https://example.com/report">자료</a>'))

    def test_broken_refs_and_missing_fallback(self):
        good=render('line-reveal',EXAMPLES['line-reveal'],'ca-safe')
        self.assertTrue(validate(good.replace('for="ca-safe-pause"','for="missing"')))
        self.assertIn('Missing reduced-motion fallback',validate(good.replace('prefers-reduced-motion','prefers-unknown')))
        self.assertIn('Missing print fallback',validate(good.replace('@media print','@media screen')))

    def test_catalog_source_paths_and_status(self):
        catalog=json.loads((ROOT/'references/motion-catalog.yaml').read_text(encoding='utf-8'))
        active=[p for p in catalog['patterns'] if p['status']=='implemented']
        self.assertEqual(set(FIELDS),{p['id'] for p in active})
        self.assertEqual(set(FIELDS),set(EXAMPLES))
        for item in active:self.assertTrue((ROOT/item['file']).exists())
        self.assertTrue(any(x['status']=='planned' for x in catalog['patterns']))

    def test_build_uses_renderer_exactly(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);manifest=build(path)
            self.assertEqual(13,manifest['patterns'])
            self.assertEqual(render('line-reveal',EXAMPLES['line-reveal'],'ca-demo-00'),(path/'line-reveal.macro.html').read_text(encoding='utf-8'))
            self.assertIn('window.CA_GALLERY=',(path/'gallery.html').read_text(encoding='utf-8'))
            self.assertFalse(manifest['confluence_verified'])

if __name__=='__main__':unittest.main()
