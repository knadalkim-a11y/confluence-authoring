"""Spec-driven visuals: validation errors an author needs, model correctness, output modes."""
from pathlib import Path
import copy, json, sys, unittest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from visual_spec import build, SpecError, fluid_schedule, decimals_of
from monitoring_cases import fluid_queue
from build_visual import make
from validate_html_macro import validate

EXAMPLES = sorted((ROOT / 'examples/visuals').glob('*.json'))


def load(name):
    return json.loads((ROOT / 'examples/visuals' / name).read_text(encoding='utf-8'))


class VisualSpecTests(unittest.TestCase):
    def test_examples_build_and_lint(self):
        self.assertGreaterEqual(len(EXAMPLES), 6)
        for f in EXAMPLES:
            with self.subTest(f=f.name):
                frag, info = make(json.loads(f.read_text(encoding='utf-8')), 'ca-spec-x')
                self.assertEqual(validate(frag), [])
                self.assertEqual(frag.count('<script>'), 1 if info['live'] else 0)
                self.assertIn('data-ca-narrow', frag)
                self.assertNotRegex(json.dumps(info['data']['captions'], ensure_ascii=False), r'\{[^{}]*\}')

    def test_mode_follows_situation(self):
        self.assertTrue(build(load('support-backlog.json'))['live'])        # accumulation over time
        self.assertFalse(build(load('quarterly-revenue.json'))['live'])     # a comparison is read, not watched
        self.assertFalse(build(load('project-timeline.json'))['live'])
        s = load('lead-time-trend.json'); s['captions'] = []
        self.assertFalse(build(s)['live'])                                   # a trend without a story stays static

    def test_honesty_fields_required(self):
        for key in ('source', 'data_kind', 'claim'):
            s = load('quarterly-revenue.json'); del s[key]
            with self.subTest(key=key), self.assertRaises(SpecError):
                build(s)

    def test_placeholders_never_pass_through(self):
        s = load('support-backlog.json'); s['captions'][-1]['text'] = '남은 백로그 {queue_ending}건'
        with self.assertRaises(SpecError):
            build(s)
        s = load('lead-time-trend.json')
        self.assertIn('2.4일', build(s)['data']['captions'][-1][2])         # Hangul keys resolve

    def test_unknown_event_and_unreadable_captions(self):
        s = load('support-backlog.json'); s['captions'][1]['at'] = 'change:9'
        with self.assertRaises(SpecError):
            build(s)
        s = load('support-backlog.json'); s['captions'].insert(2, {'at': 5.05, 'text': '거의 동시에 나오는 두 번째 자막은 읽을 시간이 없다.'})
        with self.assertRaises(ValueError):
            build(s)

    def test_flow_bottleneck_rules(self):
        s = load('order-pipeline.json'); s['stages'][0]['capacity'] = 500  # narrowest stage simply becomes the bottleneck
        self.assertEqual(build(s)['data']['lanes'][0]['b'], 0)
        s = load('order-pipeline.json'); s['stages'][1]['capacity'] = 700  # above the bottleneck (600) but below peak inflow (900)
        with self.assertRaises(SpecError):
            build(s)
        s = load('order-pipeline.json'); s['stages'][1]['name'] = '재고 확인 및 출고 준비'; del s['stages'][1]['short']
        with self.assertRaises(SpecError):
            build(s)

    def test_flow_model_matches_reference(self):
        p = dict(before_rate=200, after_rate=600, application_capacity=300, change_time=4.0, horizon=10.0)
        a = fluid_queue(p); b = fluid_schedule([[0, 200], [4.0, 600]], 300, 10.0)
        self.assertEqual([round(r['q'], 6) for r in a], [round(r['q'], 6) for r in b])
        info = build(load('support-backlog.json')); four, five = info['numeric']['lanes']
        self.assertAlmostEqual(four['queue_end'], 150)    # +20/day for 10 days, -10/day for 5 days
        self.assertAlmostEqual(five['queue_end'], 0)

    def test_decimals_follow_author_precision(self):
        self.assertEqual(decimals_of([11.2, 12.8, 16]), 1)
        self.assertEqual(decimals_of([3, 12]), 0)
        info = build(load('quarterly-revenue.json')); self.assertEqual(info['data']['decimals'], 1)

    def test_unknown_keys_rejected(self):
        s = load('quarterly-revenue.json'); s['colour'] = 'red'
        with self.assertRaises(SpecError):
            build(s)


if __name__ == '__main__':
    unittest.main()
