"""Regression gates for mechanisms, not a visual-equivalence score."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mechanism_scenes import cascade_model, event_model
from reference_scene import ROOT
from monitoring_cases import build_case
from validate_html_macro import validate

class MechanismTests(unittest.TestCase):
    def setUp(self):
        self.cases=json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases']
        self.event=event_model(next(c['params'] for c in self.cases if c['id']=='event-loop'))
    def test_routes_do_not_select_excluded_server(self):
        m=cascade_model()
        for r in m['routes']:
            if r['target'] is not None:self.assertLess(r['at'],m['failures'][r['target']])
    def test_route_distribution_is_balanced_in_each_epoch(self):
        m=cascade_model()
        bounds=[0,*m['failures']]
        for a,b in zip(bounds,bounds[1:]):
            targets=[i for i,f in enumerate(m['failures']) if a<f]
            counts=[sum(a<=r['at']<b and r['target']==i for r in m['routes']) for i in targets]
            self.assertLessEqual(max(counts)-min(counts),1)
    def test_no_target_after_final_exclusion(self):
        m=cascade_model()
        self.assertTrue(all(r['target'] is None for r in m['routes'] if r['at']>=m['failures'][-1]))
    def test_no_js_overlap(self):
        for a,b in zip(self.event['tasks'],self.event['tasks'][1:]):self.assertLessEqual(a['end'],b['start']+1e-9)
    def test_cpu_blocks_only_its_execution_window(self):
        m=self.event
        for t in m['tasks']:
            if t['kind']!='cpu':self.assertFalse(t['start']<m['block_end'] and t['end']>m['block_start'])
    def test_io_completes_while_js_is_blocked(self):
        m=self.event;self.assertTrue(any(m['block_start']<i['finish']<m['block_end'] for i in m['io']))
    def test_completed_io_callback_waits(self):
        m=self.event;t=next(t for t in m['tasks'] if t['kind']=='callback' and t['ready']>m['block_start'])
        self.assertLess(t['ready'],m['block_end']);self.assertGreaterEqual(t['start'],m['block_end'])
    def test_no_new_io_submission_during_cpu_block(self):
        m=self.event
        for t in m['io']:self.assertFalse(m['block_start']<=t['start']<m['block_end'])
    def test_all_11_requests_finish_and_queue_drains(self):
        self.assertEqual(self.event['states'][-1]['done'],11);self.assertEqual(self.event['states'][-1]['queued'],0)
    def test_invalid_event_window(self):
        with self.assertRaises(ValueError):event_model({'block_start':0,'block_end':3,'horizon':5})
    def test_19_speed_variants_preserve_model(self):
        for c in self.cases:
            with self.subTest(case=c['id']):
                base,model=build_case(c,'ca-quality-test',1)
                for speed in (1.25,1.5):
                    html,m=build_case(c,'ca-quality-test',speed)
                    self.assertEqual(model,m);self.assertFalse(validate(html))
                    self.assertIn(f'--duration:{18/speed}s',html)
    def test_invalid_speed(self):
        for speed in (True,0,2,float('nan')):
            with self.assertRaises(ValueError):build_case(self.cases[0],'ca-test',speed)

if __name__=='__main__':unittest.main()
