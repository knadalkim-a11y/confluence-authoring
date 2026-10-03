"""Live runtime contract: model binding, static fallback parity, script safety, lint."""
from pathlib import Path
import copy,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from monitoring_cases import (build_case,pool_model,pool_live_data,pipeline_live_data,bounded_live_data,cpu_live_data,
                              cpu_scenarios,fluid_queue,live_checks,LIVE_BUILDERS)
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
  meta=copy.deepcopy(CASES['memory-leak']);meta['runtime']='live'
  with self.assertRaises(ValueError):build_case(meta,'ca-live-x')
  meta['runtime']='canvas'
  with self.assertRaises(ValueError):build_case(meta,'ca-live-y')
 def test_determinism(self):
  a,_=build_case(CASES['thread-pool'],'ca-live-d');b,_=build_case(CASES['thread-pool'],'ca-live-d');self.assertEqual(a,b)

 def test_every_live_case_static_parity_and_determinism(self):
  for c in LIVE:
   with self.subTest(id=c['id']):
    data=LIVE_BUILDERS[c['id']](c['params'])[0];a=node_static(data)
    f,_=build_case(c,'ca-live-p');self.assertIn(a['svg'],f);self.assertEqual(f,build_case(c,'ca-live-p')[0])
    times=[x[0] for x in data['captions']];self.assertEqual(times,sorted(times));self.assertEqual(times[0],0)
    self.assertIn(data['captions'][-1][2],f)
    self.assertTrue(all(r>0 for _,r in data['rate']));self.assertEqual([t for t,_ in data['rate']],sorted({t for t,_ in data['rate']}))
    chk=live_checks(c['id'],c['params']);self.assertEqual(len(chk['samples']),6)
    for label,at in chk['annotations']:self.assertIn(label,a['svg'])   # final scene shows every annotation
 def test_pipeline_model_binding(self):
  p=CASES['pipeline-bottleneck']['params'];data,_,_,_,num=pipeline_live_data(p);rows=fluid_queue(p,steps=200);S=data['series']
  self.assertAlmostEqual(S['q'][-1],rows[-1]['q']);self.assertAlmostEqual(S['q'][-1],1800)
  unit=data['unit'];self.assertEqual(unit,20);tok=data['tokens']
  self.assertEqual(len(tok),int(rows[-1]['incoming']//unit));self.assertFalse(any(t[2] for t in tok))
  served=[t for t in tok if t[1] is not None];self.assertEqual(len(served),int(rows[-1]['served']//unit+1e-9))
  self.assertEqual([t[1] for t in served],sorted(t[1] for t in served))           # FIFO departures
  self.assertTrue(all(t[1]>=t[0] for t in served))
  ev=data['events'];self.assertAlmostEqual(ev['t_wait1'],p['change_time']+1);self.assertAlmostEqual(ev['t_wait2'],p['change_time']+2)
  self.assertIn([p['change_time'],'②'],[x[:2] for x in data['captions']]);self.assertIn(ev['t_wait1'],[x[0] for x in data['captions']])
  before=[t for t in tok if t[0]<p['change_time']];self.assertTrue(all(abs(t[1]-t[0])<1e-3 for t in before))   # no wait below capacity
 def test_bounded_model_binding(self):
  p=CASES['bounded-queue']['params'];data,_,_,_,num=bounded_live_data(p);S=data['series'];unit=data['unit']
  self.assertAlmostEqual(S['qb'][-1],p['queue_limit']);self.assertAlmostEqual(S['qu'][-1],600);self.assertAlmostEqual(num['rejected'],592)
  self.assertAlmostEqual(num['overload_rejection_fraction'],592/1200)
  self.assertLessEqual(max(S['qb']),p['queue_limit']+1e-9)
  tb=data['tokens_b'];tu=data['tokens_u'];self.assertEqual(len(tb),len(tu));self.assertEqual([t[0] for t in tb],[t[0] for t in tu])
  rej=sum(t[2] for t in tb);self.assertLessEqual(abs(rej*unit-num['rejected']),unit)   # token rejections track the fluid balance
  self.assertFalse(any(t[2] for t in tu))
  # Continuous fill time is 4.08 s; the fluid model integrates in 0.05 s steps, so allow one step.
  self.assertLessEqual(abs(data['events']['t_full']-(p['change_time']+p['queue_limit']/(p['after_rate']-p['capacity']))),0.05+1e-9)
  self.assertIn(data['events']['t_full'],[x[0] for x in data['captions']])
 def test_bounded_requires_overload(self):
  p=copy.deepcopy(CASES['bounded-queue']['params']);p['after_rate']=90
  with self.assertRaises(ValueError):bounded_live_data(p)
 def test_cpu_series_and_verdict_timing(self):
  data=cpu_live_data({})[0];sc=cpu_scenarios();H=data['axes']['end'];ts=data['series']['t']
  for s,x in zip(data['services'],sc):
   self.assertEqual(s['cpu'],[round(x['cpu'](t/H),3) for t in ts]);self.assertEqual(s['p99'],[round(x['p99'](t/H),3) for t in ts])
  ev=data['events'];self.assertEqual(data['services'][2]['verdict'][0],ev['cpu_saturated']);self.assertEqual(data['services'][1]['verdict'][0],ev['p99_plateau'])
  for t in ev.values():self.assertIn(t,[x[0] for x in data['captions']])
  st=node_static(data)['svg'];self.assertIn('연산 포화 의심',st);self.assertIn('대기 의심',st)
  # Verdict must not be in a frame drawn before its event (same draw code, Node).
  self.assertNotIn('대기 의심',static_at(data,ev['p99_plateau']-0.5));self.assertNotIn('연산 포화 의심',static_at(data,ev['cpu_saturated']-0.5))

def static_at(data,t,width=720):
 import shutil,subprocess,tempfile
 from live_scene import core_js
 program=core_js(data['scene'])+('\nvar D=JSON.parse(require("fs").readFileSync(0,"utf8"));var sc=CA_SCENES[D.scene](D,CA_KIT,CA_GRAMMARS);'
  'process.stdout.write(sc.draw(%r,sc.geom(%d)));'%(t,width))
 with tempfile.TemporaryDirectory() as tmp:
  f=Path(tmp)/'at.js';f.write_text(program,encoding='utf-8')
  return subprocess.run([shutil.which('node'),str(f)],input=json.dumps(data),capture_output=True,text=True,check=True).stdout

if __name__=='__main__':unittest.main()
