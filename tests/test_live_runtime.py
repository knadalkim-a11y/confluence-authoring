"""Live runtime contract: model binding, static fallback parity, script safety, lint."""
from pathlib import Path
import copy,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from monitoring_cases import (build_case,pool_model,pool_live_data,pipeline_live_data,bounded_live_data,cpu_live_data,
                              cpu_scenarios,fluid_queue,live_checks,LIVE_BUILDERS,caption_walls,caption_need,CAPTION_MAX_CHARS)
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
  self.assertEqual(a,b);self.assertIn('0/8',a['svg']);self.assertIn('스레드 풀',a['svg'])
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
  meta=copy.deepcopy(CASES['gc-pause']);meta['runtime']='live'   # a case with no live builder
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
  p=CASES['pipeline-bottleneck']['params'];data,_,_,_,num=pipeline_live_data(p);rows=fluid_queue(p,steps=200);l=data['lanes'][0]
  self.assertEqual(data['scene'],'flow');self.assertAlmostEqual(l['q'][-1],rows[-1]['q']);self.assertAlmostEqual(l['q'][-1],1800)
  unit=data['unit'];tok=l['tokens']
  self.assertEqual(len(tok),int(rows[-1]['incoming']//unit));self.assertFalse(any(t[2] for t in tok))
  served=[t for t in tok if t[1] is not None];self.assertEqual(len(served),int(rows[-1]['served']//unit+1e-9))
  self.assertEqual([t[1] for t in served],sorted(t[1] for t in served))           # FIFO departures
  self.assertTrue(all(t[1]>=t[0] for t in served))
  ev=num['events'];self.assertAlmostEqual(ev['wait:1'],p['change_time']+1);self.assertAlmostEqual(ev['wait:2'],p['change_time']+2)
  times=[x[0] for x in data['captions']];self.assertTrue(any(abs(p['change_time']-x)<1e-6 for x in times));self.assertTrue(any(abs(ev['wait:1']-x)<1e-6 for x in times))
  before=[t for t in tok if t[0]<p['change_time']];self.assertTrue(all(abs(t[1]-t[0])<1e-3 for t in before))   # no wait below capacity
 def test_bounded_model_binding(self):
  p=CASES['bounded-queue']['params'];data,_,_,_,num=bounded_live_data(p);u,b=data['lanes'];unit=data['unit']
  self.assertAlmostEqual(b['q'][-1],p['queue_limit']);self.assertAlmostEqual(u['q'][-1],600);self.assertAlmostEqual(num['rejected'],592)
  self.assertAlmostEqual(num['overload_rejection_fraction'],592/1200);self.assertLessEqual(max(b['q']),p['queue_limit']+1e-9)
  self.assertEqual([t[0] for t in b['tokens']],[t[0] for t in u['tokens']])
  rej=sum(t[2] for t in b['tokens']);self.assertLessEqual(abs(rej*unit-num['rejected']),unit)   # token rejections track the fluid balance
  self.assertFalse(any(t[2] for t in u['tokens']))
  # Continuous fill time is 4.08 s; the fluid model integrates in 0.05 s steps, so allow one step.
  self.assertLessEqual(abs(num['events']['full@1']-(p['change_time']+p['queue_limit']/(p['after_rate']-p['capacity']))),0.05+1e-9)
  self.assertTrue(any(abs(num['events']['full@1']-x[0])<1e-6 for x in data['captions']))
 def test_bounded_requires_overload(self):
  p=copy.deepcopy(CASES['bounded-queue']['params']);p['after_rate']=90
  with self.assertRaises(ValueError):bounded_live_data(p)
 def test_cpu_series_and_verdict_timing(self):
  data,_,_,_,num=cpu_live_data({});sc=cpu_scenarios();H=data['time']['end'];E=num['events']
  for g,x in zip(data['groups'],sc):
   cpu=g['panels'][0]['series'][0];p99=g['panels'][1]['series'][0]
   self.assertEqual(cpu['v'],[round(x['cpu'](t/H),3) for t in cpu['t']]);self.assertEqual(p99['v'],[round(x['p99'](t/H),3) for t in p99['t']])
  self.assertEqual(data['groups'][2]['pill'][-1][0],E['cpu_saturated']);self.assertEqual(data['groups'][1]['pill'][-1][0],E['p99_plateau'])
  for t in E.values():self.assertTrue(any(abs(t-x[0])<1e-6 for x in data['captions']))
  st=node_static(data)['svg'];self.assertIn('CPU 100%에 붙었다',st);self.assertIn('CPU는 노는데 느리다',st)
  self.assertNotIn('노는데 느리다',static_at(data,E['p99_plateau']-0.5));self.assertNotIn('100%에 붙었다',static_at(data,E['cpu_saturated']-0.5))
 def test_captions_readable_at_default_speed(self):
  # Every caption but the last (which stays after playback) is on screen long enough to read.
  for c in LIVE:
   with self.subTest(id=c['id']):
    d=LIVE_BUILDERS[c['id']](c['params'])[0];end=live_checks(c['id'],c['params'])['end']
    walls=caption_walls(d['captions'],d['rate'],end)
    for cap,w in list(zip(d['captions'],walls))[:-1]:self.assertGreaterEqual(w+1e-6,caption_need(cap[2]),cap)
    self.assertTrue(all(len(x[2])<=CAPTION_MAX_CHARS for x in d['captions']))
 def test_palette_text_contrast(self):
  kit=(ROOT/'visuals/live/kit.js').read_text()
  C=dict(re.findall(r"(\w+):'(#[0-9a-f]{3,6})'",kit.split('var PILL')[0]))
  for key in ['ink','text','muted','blueText','redText','amberText','greenText','purpleText']:
   with self.subTest(key=key):self.assertGreaterEqual(contrast(C[key],'#fff'),4.5)
  for kind,bg,fg in re.findall(r"(\w+):\['(#[0-9a-f]{3,6})','(#[0-9a-f]{3,6})'\]",kit.split('var PILL')[1].split(';')[0]):
   with self.subTest(pill=kind):self.assertGreaterEqual(contrast(fg,bg),4.5)
 def test_kit_motion_parts(self):
  """K.ortho never leaves a diagonal step; K.at walks a polyline at constant distance; K.ease is 0..1."""
  import random,shutil,subprocess
  kit=(ROOT/'visuals/live/kit.js').read_text(encoding='utf-8');random.seed(7)
  cases=[[[random.uniform(0,600),random.uniform(0,400)] for _ in range(random.randint(2,5))] for _ in range(200)]
  prog=kit+'\nvar K=CA_KIT,C=%s,out=[];C.forEach(function(p,i){out.push(K.ortho(p,i%%2?"v":"h"));});'%json.dumps(cases)+\
   'process.stdout.write(JSON.stringify({o:out,at:K.at([[0,0],[10,0],[10,10]],15),e:[0,.1,.2,.3,.35,.5].map(function(t){return K.ease(t,0,.35);}),'+\
   'w:K.wire([[0,0],[5,0]],"#000"),t:K.token(1,2,"a<b",3,"#000")}));'
  r=json.loads(subprocess.run([shutil.which('node'),'-e',prog],capture_output=True,text=True,check=True).stdout)
  for pts,src in zip(r['o'],cases):
   self.assertEqual(pts[0],src[0]);self.assertEqual(pts[-1],src[-1])
   for a,b in zip(pts,pts[1:]):self.assertTrue(abs(a[0]-b[0])<=0.5 or abs(a[1]-b[1])<=0.5,(a,b))
  self.assertEqual([r['at']['x'],r['at']['y']],[10,5]);e=r['e'];self.assertEqual(e[0],0);self.assertEqual(e[-1],1);self.assertEqual(e,sorted(e))
  self.assertIn('data-wire="1"',r['w']);self.assertIn('data-token="a&lt;b"',r['t'])

 def test_connectors_are_orthogonal_wires(self):
  """Scenes that draw connectors use K.wire, and no wire has a diagonal segment at any width."""
  from visual_spec import build
  datas=[LIVE_BUILDERS['cluster-cascade'](CASES['cluster-cascade']['params'])[0]]
  for f in ('ai-agent-request','rag-indexing','ai-adoption-approval'):
   datas.append(build(json.loads((ROOT/'examples/visuals'/f'{f}.json').read_text(encoding='utf-8')))['data'])
  for data in datas:
   for w in (720,600,360):
    for t in (0.3,data.get('end_h',data.get('time',{}).get('end',1))/2):
     svg=static_at(data,t,w);ws=re.findall(r'data-wire="1" points="([^"]+)"',svg);self.assertTrue(ws,(data['scene'],w))
     self.assertNotRegex(svg,r'<path d="M[\d.]+ [\d.]+L[\d.]+ [\d.]+(L[\d.]+ [\d.]+){0,2}" fill="none"')   # no hand-made connector
     for pts in ws:
      q=[float(x) for x in pts.split()];xy=list(zip(q[::2],q[1::2]))
      for a,b in zip(xy,xy[1:]):self.assertTrue(abs(a[0]-b[0])<=0.6 or abs(a[1]-b[1])<=0.6,(data['scene'],w,a,b))

 def test_two_static_scenes(self):
  for c in LIVE:
   with self.subTest(id=c['id']):
    f,_=build_case(c,'ca-live-n');self.assertEqual(f.count('data-ca-static'),2);self.assertIn('data-ca-narrow',f)

def contrast(a,b):
 def lum(h):
  h=h.lstrip('#');h=''.join(x*2 for x in h) if len(h)==3 else h
  v=[int(h[i:i+2],16)/255 for i in (0,2,4)];v=[x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4 for x in v]
  return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2]
 la,lb=sorted([lum(a),lum(b)],reverse=True);return (la+0.05)/(lb+0.05)

def static_at(data,t,width=720):
 import shutil,subprocess,tempfile
 from live_scene import core_js
 program=core_js(data['scene'])+('\nvar D=JSON.parse(require("fs").readFileSync(0,"utf8"));var sc=CA_SCENES[D.scene](D,CA_KIT,CA_GRAMMARS);'
  'process.stdout.write(sc.draw(%r,sc.geom(%d)));'%(t,width))
 with tempfile.TemporaryDirectory() as tmp:
  f=Path(tmp)/'at.js';f.write_text(program,encoding='utf-8')
  return subprocess.run([shutil.which('node'),str(f)],input=json.dumps(data),capture_output=True,text=True,check=True).stdout

if __name__=='__main__':unittest.main()
