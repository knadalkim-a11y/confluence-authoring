"""Numerical, rendering and contract regression for the article reference suite."""
from pathlib import Path
import copy,hashlib,json,math,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from monitoring_cases import build_case,stats,fluid_queue,pool_model,pool_state,BUILDERS
from reference_scene import ReferenceScene,document,simplify_track
from validate_html_macro import validate
CASES=json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases']
BY_ID={x['id']:x for x in CASES}

class MonitoringSuiteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rendered={c['id']:build_case(c,'ca-test-'+str(i)) for i,c in enumerate(CASES)}
 def test_inventory(self):
  self.assertEqual(sum(c['in_article'] for c in CASES),18);self.assertEqual(len(CASES),19);self.assertEqual(len(BY_ID),19);self.assertEqual(set(BY_ID),set(BUILDERS))
 def test_all_macros_lint(self):
  for id,(fragment,_) in self.rendered.items():
   with self.subTest(id=id):self.assertEqual(validate(fragment),[])
 def test_exact_preview_fragment(self):
  for fragment,_ in self.rendered.values():self.assertIn(fragment,document(fragment))
 def test_two_instances_and_collision(self):
  a,_=build_case(BY_ID['cpu-latency'],'ca-one');b,_=build_case(BY_ID['cpu-latency'],'ca-two')
  self.assertEqual(validate(a+b),[]);self.assertIn('Duplicate prefix',validate(a+a))
 def test_multiple_svg_ids(self):
  fragment=self.rendered['traffic-patterns'][0];ids=re.findall(r'id="([^"]+)"',fragment)
  self.assertEqual(len(ids),len(set(ids)));self.assertEqual(fragment.count('<svg'),4)
 def test_distribution_values(self):
  n=self.rendered['percentile-comparison'][1]
  self.assertEqual(n['서버 A'],dict(n=40,mean=100.0,p50=100,p95=115,p99=130))
  self.assertEqual(n['서버 B'],dict(n=40,mean=100.0,p50=22,p95=470,p99=850))
 def test_percentile_definition(self):
  self.assertEqual(stats([10,20],[99,1])['p99'],10);self.assertEqual(stats([10,20],[98,2])['p99'],20)
 def test_invalid_distribution(self):
  for a,b in [([1,1],[1,2]),([1,2],[0,0]),([1,2],[1,-1]),([2,1],[1,1]),([1,2],[True,1])]:
   with self.subTest(values=a,counts=b),self.assertRaises(ValueError):stats(a,b)
 def test_pipeline_accounting(self):
  p=BY_ID['pipeline-bottleneck']['params'];rows=fluid_queue(p)
  self.assertAlmostEqual(rows[-1]['q'],1800);self.assertAlmostEqual(rows[-1]['incoming'],4400);self.assertAlmostEqual(rows[-1]['served'],2600)
  for row in rows:self.assertAlmostEqual(row['incoming'],row['served']+row['q']+row['rejected'],places=6)
 def test_queue_grid_independence(self):
  p=copy.deepcopy(BY_ID['pipeline-bottleneck']['params']);p['change_time']=4.137
  self.assertAlmostEqual(fluid_queue(p,steps=50)[-1]['q'],fluid_queue(p,steps=173)[-1]['q'],places=6)
 def test_bounded_conservation(self):
  p=BY_ID['bounded-queue']['params'];rows=fluid_queue(p,p['queue_limit'])
  for row in rows:
   self.assertLessEqual(row['q'],8+1e-8);self.assertGreaterEqual(row['q'],0);self.assertAlmostEqual(row['incoming'],row['served']+row['q']+row['rejected'],places=6)
  self.assertAlmostEqual(rows[-1]['rejected'],592);self.assertAlmostEqual(rows[-1]['q'],8)
 def test_pool_conservation(self):
  p=BY_ID['thread-pool']['params'];jobs=pool_model(p)
  times=sorted(set([0,p['horizon']]+[j[k] for j in jobs for k in ['arrive','start','end']]))
  for t in times:
   v=pool_state(jobs,t+1e-9);self.assertEqual(v['arrived'],v['completed']+v['active']+v['queued']);self.assertLessEqual(v['active'],p['workers'])
  self.assertEqual(pool_state(jobs,p['horizon'])['completed'],len(jobs))
 def test_pool_worker_exclusion(self):
  jobs=pool_model(BY_ID['thread-pool']['params'])
  for slot in range(8):
   row=[j for j in jobs if j['slot']==slot]
   for a,b in zip(row,row[1:]):self.assertLessEqual(a['end'],b['start'])
 def test_cascade_distribution(self):
  data=self.rendered['cluster-cascade'][1]['shares_sum'];self.assertEqual([round(v,9) for _,v in data],[1,1,1,0])
 def test_cache_identity(self):
  d=self.rendered['cache-stampede'][1]
  for (t,hit),(qtime,qps) in zip(d['hit'],d['qps']):self.assertEqual(t,qtime);self.assertAlmostEqual(qps,d['total']*(1-hit/100))
  self.assertAlmostEqual(d['qps'][0][1],150)
 def test_survivorship_denominators(self):
  d=self.rendered['survivorship-bias'][1]['populations']
  for row in d.values():self.assertEqual(row['success']+row['failure'],1000)
  self.assertEqual(d['before']['p99'],140);self.assertEqual(d['after']['p99'],75)
 def test_quota_accounting(self):
  d=self.rendered['cpu-throttling'][1]
  for _,used,blocked,other in d['rows']:self.assertEqual(used+blocked+other,d['period']);self.assertLessEqual(used,d['quota'])
 def test_timeout_intervals(self):
  d=self.rendered['timeout-mismatch'][1];self.assertEqual(d['unobserved_work'],2);self.assertEqual(d['request_count'],1)
 def test_postmortem_intervals(self):
  self.assertEqual(self.rendered['postmortem-timeline'][1]['intervals'],{'감지 공백':18,'알림 → 복구':32,'알림 → 대응 시작':3,'대응 시작 → 복구':29})
 def test_utilization_model(self):
  vals=self.rendered['utilization-wait'][1]['normalized_wait'];self.assertAlmostEqual(vals[-1][1],19);self.assertAlmostEqual(vals[2][1],4)
 def test_slow_burn(self):self.assertAlmostEqual(self.rendered['slow-degradation'][1]['growth_percent'],72.2222222222)
 def test_escape_untrusted_text(self):
  meta=copy.deepcopy(BY_ID['pipeline-bottleneck']);meta['title']='</h3><script>alert(1)</script>';fragment,_=build_case(meta,'ca-escape')
  self.assertNotIn('<script',fragment);self.assertIn('&lt;script&gt;',fragment);self.assertEqual(validate(fragment),[])
 def test_unknown_and_invalid_inputs(self):
  for key,value in [('after_rate',float('nan')),('before_rate',-1),('application_capacity',0)]:
   meta=copy.deepcopy(BY_ID['pipeline-bottleneck']);meta['params'][key]=value
   with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):build_case(meta)
  meta=copy.deepcopy(BY_ID['pipeline-bottleneck']);meta['params']['unexpected']=2
  with self.assertRaises(ValueError):build_case(meta)
 def test_prefix_validation(self):
  for prefix in ['x','1bad','x;body','x"']: 
   with self.subTest(prefix=prefix),self.assertRaises(ValueError):build_case(BY_ID['traffic-patterns'],prefix)
 def test_simplification_preserves_holds(self):
  f=[(0,'transform:rotate(0deg)'),(.3,'transform:rotate(540deg)'),(.5,'transform:rotate(540deg)'),(.6,'transform:rotate(540deg)'),(1,'transform:rotate(1260deg)')]
  result=simplify_track(f);self.assertIn((.3,'transform:rotate(540deg)'),result);self.assertIn((.6,'transform:rotate(540deg)'),result);self.assertEqual(len(result),4)
 def test_simplification_linear(self):
  self.assertEqual(simplify_track([(0,'width:0px'),(.25,'width:25px'),(.5,'width:50px'),(1,'width:100px')]),[(0,'width:0px'),(1,'width:100px')])
 def test_scene_track_contract(self):
  for f in [[],[(0,'opacity:0'),(0,'opacity:1')],[(-1,'opacity:1'),(1,'opacity:1')]]:
   with self.assertRaises(ValueError):ReferenceScene().track(f)
 def test_bonus_separate(self):self.assertFalse(BY_ID['gc-pause']['in_article'])
 def test_no_remote_runtime(self):
  for id,(fragment,_) in self.rendered.items():
   with self.subTest(id=id):
    self.assertNotRegex(fragment,r'<(?:iframe|link|image)\b');self.assertNotRegex(fragment,r'(?:src|srcdoc)=')
    if BY_ID[id].get('runtime')=='live':self.assertEqual(fragment.count('<script>'),1)
    else:self.assertNotIn('<script',fragment)
 def test_generator_determinism(self):
  a,_=build_case(BY_ID['pipeline-bottleneck'],'ca-stable');b,_=build_case(BY_ID['pipeline-bottleneck'],'ca-stable');self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
