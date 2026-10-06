"""The reference pack against the spec path: the flow model and the frozen trend fixtures match the case builders."""
from pathlib import Path
import json, sys, unittest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(1, str(ROOT.parent / 'scripts'))
from monitoring_cases import fluid_queue, postmortem_spec, slow_spec
from visual_spec import fluid_schedule


class ReferenceSpecs(unittest.TestCase):
    def test_flow_model_matches_reference(self):
        p = dict(before_rate=200, after_rate=600, application_capacity=300, change_time=4.0, horizon=10.0)
        a = fluid_queue(p); b = fluid_schedule([[0, 200], [4.0, 600]], 300, 10.0)
        self.assertEqual([round(r['q'], 6) for r in a], [round(r['q'], 6) for r in b])

    def test_frozen_fixtures_match_builders(self):
        cases = {c['id']: c for c in json.loads((ROOT / 'examples/monitoring-cases.json').read_text())['cases']}
        for name, fn in (('postmortem-timeline', postmortem_spec), ('slow-degradation', slow_spec)):
            frozen = json.loads((ROOT.parent / 'tests/fixtures' / f'{name}.json').read_text(encoding='utf-8'))
            self.assertEqual(frozen, json.loads(json.dumps(fn(cases[name]['params'])[0])))


if __name__ == '__main__':
    unittest.main()
