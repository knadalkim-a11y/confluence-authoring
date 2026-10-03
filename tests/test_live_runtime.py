"""Live runtime contract: model binding, static fallback parity, script safety, lint."""
from pathlib import Path
import copy,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from monitoring_cases import build_case,pool_model,pool_live_data,LIVE_BUILDERS
from live_scene import node_static,json_for_script,core_js
from validate_html_macro import validate
CASES={c['id']:c for c in json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases']}
LIVE=[c for c in CASES.values() if c.get('runtime')=='live']

class LiveRuntimeTests(unittest.TestCase):
 def test_inventory(self):
  self.assertEqual({c['id'] for c in LIVE},set(LIVE_BUILDERS))
 def test_lint_and_single_runtime(self):
  for c in LIVE:
   f,_=build_case(c,'ca-live-a');self.assertEqual(validate(f),[]);self.assertEqual(f.count('<script>'),1)
   self.assertTrue(f.split('<script>')[1].startswith('/*ca-live-runtime v1*/'))
   self.assertIn('data-ca-static',f);self.assertNotRegex(f,r'<(?:iframe|link|image)\b|(?:src|srcdoc)=')
 def test_two_instances_isolated(self):
  c=LIVE[0];a,_=build_case(c,'ca-live-one');b,_=build_case(c,'ca-live-two')
  self.assertEqual(validate(a+b),[]);self.assertIn('Duplicate prefix',validate(a+a))
  self.assertIn('[data-ca-prefix="ca-live-one"]',a);self.assertNotIn('ca-live-two',a)
 def test_model_binding(self):
  p=CASES['thread-pool']['params'];data,_,_,_,num=pool_live_data(p);jobs=pool_model(p)
  self.assertEqual(len(data['jobs']),len(jobs))
  for row,j in zip(data['jobs'],jobs):self.assertEqual(row,[round(j['arrive'],6),round(j['start'],6),round(j['end'],6),j['slot'],j['service']])
  ev=data['events'];waits=[j for j in jobs if j['wait']>1e-9]
  self.assertAlmostEqual(ev['t_queue'],min(j['arrive'] for j in waits));self.assertAlmostEqual(ev['t_drain'],max(j['start'] for j in waits))
  self.assertEqual(ev['q_max'],14);self.assertAlmostEqual(num['live']['max_response'],3.6)
 def test_captions_bound_to_events(self):
  data=pool_live_data(CASES['thread-pool']['params'])[0];times=[c[0] for c in data['captions']]
  self.assertEqual(times,sorted(times));self.assertIn(data['events']['t_queue'],times)
  self.assertIn(data['params']['slow_start'],times);self.assertIn(data['params']['recovery'],times)
  self.assertTrue(all(r>0 for _,r in data['rate']))
 def test_no_queue_variant(self):
  p=copy.deepcopy(CASES['thread-pool']['params']);p['slow_service']=1.0   # 6.7/s x 1.0s < 8 workers
  data=pool_live_data(p)[0];self.assertIsNone(data['events']['t_queue']);self.assertEqual(data['events']['q_max'],0)
  meta=copy.deepcopy(CASES['thread-pool']);meta['params']=p;f,_=build_case(meta,'ca-live-noq');self.assertEqual(validate(f),[])
  svg=f.split('data-ca-static')[1].split('</svg>')[0];self.assertNotIn('최대 대기',svg);self.assertNotIn('대기 0.0',svg)
 def test_static_fallback_is_final_scene_of_same_code(self):
  data=pool_live_data(CASES['thread-pool']['params'])[0];a=node_static(data);b=node_static(data)
  self.assertEqual(a,b);self.assertIn('최대 대기 14건',a['svg']);self.assertIn('0/8',a['svg'])
  f,_=build_case(CASES['thread-pool'],'ca-live-s');self.assertIn(a['svg'],f)
 def test_script_data_inert(self):
  s=json_for_script({'x':'</script><!-- \u2028'});self.assertNotIn('<',s);self.assertNotIn('\u2028',s)
  meta=copy.deepcopy(CASES['thread-pool']);meta['title']='</script><script>alert(1)</script>'
  f,_=build_case(meta,'ca-live-esc');self.assertEqual(f.count('<script>'),1);self.assertEqual(validate(f),[])
 def test_validator_rejects_foreign_scripts(self):
  f,_=build_case(CASES['thread-pool'],'ca-live-v')
  self.assertTrue(validate(f.replace('/*ca-live-runtime v1*/','')))
  self.assertTrue(validate(f.replace('"use strict";','"use strict";fetch("x");')))
  self.assertTrue(validate(f+'<script>/*ca-live-runtime v1*/</script>'))
  self.assertTrue(validate(f.replace('<script>','<script src="x.js">')))
 def test_unknown_scene(self):
  with self.assertRaises(ValueError):core_js('../x')
  meta=copy.deepcopy(CASES['cpu-latency']);meta['runtime']='live'
  with self.assertRaises(ValueError):build_case(meta,'ca-live-x')
  meta['runtime']='canvas'
  with self.assertRaises(ValueError):build_case(meta,'ca-live-y')
 def test_determinism(self):
  a,_=build_case(CASES['thread-pool'],'ca-live-d');b,_=build_case(CASES['thread-pool'],'ca-live-d');self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
