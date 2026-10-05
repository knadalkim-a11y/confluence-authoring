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


    def test_funnel(self):
        info = build(load('signup-funnel.json')); f = info['data']['funnel']
        self.assertEqual(f['worst'], 3)                                   # lowest conversion: 1,900 -> 420
        self.assertEqual(f['lost'][1], 8900)
        s = load('signup-funnel.json'); s['drop'] = 'count'
        self.assertEqual(build(s)['data']['funnel']['worst'], 1)         # most people lost: 12,000 -> 3,100
        s = load('signup-funnel.json'); s['items'][2]['value'] = 5000     # a step that grows is not a funnel
        with self.assertRaises(SpecError):
            build(s)

    def test_share(self):
        info = build(load('infra-cost-share.json')); d = info['data']
        self.assertIn('−9%p', d['change']); self.assertAlmostEqual(sum(d['rows'][0]['pct']), 100)
        s = load('infra-cost-share.json'); s['rows'][0]['values'][0] = 70  # 109% is not a composition
        with self.assertRaises(SpecError):
            build(s)
        s = load('infra-cost-share.json'); s['unit'] = '억 원'             # raw values are normalised
        self.assertAlmostEqual(sum(build(s)['data']['rows'][1]['pct']), 100)

    def test_clock_timeline(self):
        info = build(load('incident-timeline.json')); d = info['data']
        self.assertEqual(d['time']['start'], 14 * 60); self.assertEqual([t['note'] for t in d['tracks']], ['3분', '7분', '19분', '9분'])
        self.assertFalse(d['legend'])
        self.assertTrue(all(':' in x[1] for x in d['ticks']))
        s = load('incident-timeline.json'); s['time'] = {'start': '23:40', 'end': '00:30'}
        s['tracks'] = [{'label': '야간 점검', 'start': '23:50', 'end': '00:20', 'status': 'active'}]; s['milestones'] = []
        d = build(s)['data']; self.assertEqual(d['tracks'][0]['b'] - d['tracks'][0]['a'], 30)   # wraps past midnight

    def test_static_kinds_mark_illustrative_data(self):
        from live_scene import node_static
        for name in ('signup-funnel.json', 'infra-cost-share.json', 'incident-timeline.json', 'quarterly-revenue.json'):
            with self.subTest(name=name):
                self.assertIn('예시 데이터', node_static(build(load(name))['data'])['svg'])

    def test_concept(self):
        """concept kind: three forms, role tones, default choreography that settles before the end."""
        for name, form, units in (('rag-before-after.json', 'compare', 2), ('agent-context-window.json', 'stack', 5), ('agent-tool-call.json', 'sequence', 8)):
            info = build(load(name)); d = info['data']
            self.assertEqual((d['scene'], d['form']), ('concept', form))
            self.assertTrue(info['live'] and info['checks']['choreo'])
            self.assertTrue(d['cues'] and all(c[2] + c[3] <= d['time']['end'] + 1e-6 for c in d['cues']))
            self.assertEqual(info['data']['labels']['data_kind'], '예시')
            frag, _ = make(load(name), 'ca-concept-test')
            self.assertEqual(validate(frag), [], name)
        self.assertEqual(len(build(load('agent-tool-call.json'))['table'][1]), 8)
        bad = load('rag-before-after.json')
        for mut, msg in ((lambda s: s.update(form='matrix'), 'form'), (lambda s: s['columns'].pop(), 'columns'),
                         (lambda s: s['columns'][0].update(tone='pink'), 'tone'), (lambda s: s['columns'][0]['items'][0].update(name='x' * 17), 'name'),
                         (lambda s: s.update(data_kind='measured'), 'data_kind')):
            spec = copy.deepcopy(bad); mut(spec)
            with self.assertRaises(SpecError, msg=msg): build(spec)
        seq = load('agent-tool-call.json'); seq['messages'][0]['to'] = 'nobody'
        with self.assertRaises(SpecError): build(seq)
        st = load('agent-context-window.json'); st['layers'][0]['size'] = 4
        with self.assertRaises(SpecError): build(st)
        static = load('agent-tool-call.json'); static['motion'] = 'none'
        info = build(static); self.assertFalse(info['live']); self.assertEqual(info['data']['cues'], [])

    def test_diagram_tones(self):
        spec = load('ai-agent-request.json'); d = build(spec)['data']
        self.assertEqual(d['groups'][0]['tone'], 'blue')
        spec['layers'][0]['nodes'][0]['tone'] = 'pink'
        with self.assertRaises(SpecError): build(spec)

    def test_diagram(self):
        r = build(load('ai-agent-request.json'))
        self.assertTrue(r['live'])                                   # steps -> a walkthrough
        self.assertFalse(build(load('rag-indexing.json'))['live'])   # structure only -> static
        self.assertEqual([r['checks']['expect'](t)['state']['step'] for t in (0, 1.5, 3.99, 4)], [0, 1, 3, 4])
        self.assertEqual(r['data']['captions'][-1][2], load('ai-agent-request.json')['claim'])
        par = build(load('ai-adoption-approval.json'))['data']['steps'][0]
        self.assertEqual(len(par['paths']), 2)                       # parallel routes in one step
        base = load('rag-indexing.json')
        cases = {
            'data_kind': (lambda s: s.update(data_kind='measured'), 'current'),
            'skip layer': (lambda s: s['layers'][0]['nodes'].append({'id': 'x', 'name': 'X'}) or s['edges'].append({'from': 'drive', 'to': 'agent'}), 'skips a layer'),
            'neighbours': (lambda s: s['layers'][0]['nodes'].append({'id': 'x', 'name': 'X'}) or s['edges'].append({'from': 'wiki', 'to': 'x'}), 'neighbours'),
            'path edge': (lambda s: s.update(steps=[{'path': ['wiki', 'vdb'], 'text': '없는 연결을 따라간다'}]), 'no connection'),
            'duplicate id': (lambda s: s['layers'][1]['nodes'].append({'id': 'wiki', 'name': 'W'}), 'used twice'),
            'too many': (lambda s: s['layers'][2]['nodes'].extend({'id': f'n{i}', 'name': 'N'} for i in range(4)), '1-4 components'),
        }
        for name, (mutate, msg) in cases.items():
            with self.subTest(name=name):
                spec = copy.deepcopy(base); mutate(spec)
                with self.assertRaisesRegex(SpecError, msg):
                    build(spec)

    def test_trend_vocabulary(self):
        # bands compute their duration, annotations fill model placeholders, between needs real series
        sys.path.insert(0, str(ROOT / 'scripts'))
        from monitoring_cases import postmortem_spec, slow_spec
        import json as _j
        cases = {c['id']: c for c in _j.loads((ROOT / 'examples/monitoring-cases.json').read_text())['cases']}
        pm = build(postmortem_spec(cases['postmortem-timeline']['params'])[0])['data']
        self.assertEqual(pm['bands'][0][2], '감지 공백 18분')
        self.assertEqual([e[2] for e in pm['events']], ['amber', 'red', 'purple', 'green'])
        sl = slow_spec(cases['slow-degradation']['params'])[0]
        self.assertEqual(build(sl)['data']['annotations'][0][3], '+72% (180ms → 310ms)')
        bad = copy.deepcopy(sl); bad['between'][0]['lower'] = '없는 선'
        with self.assertRaisesRegex(SpecError, 'series'):
            build(bad)
        bad = copy.deepcopy(sl); bad['annotations'][0]['text'] = '{없는값}'
        with self.assertRaisesRegex(SpecError, 'placeholder'):
            build(bad)

    def test_figure_footer_fits(self):
        # the exported SVG's source line wraps inside the figure (a 90-char source used to overflow)
        from live_scene import wrap_text, text_width
        for src, cut in (('출처: 사내 집계', False), ('출처: ' + '재무팀 월간 결산 보고서와 분기 검토 자료 ' * 3, False),
                         ('출처: ' + '재무팀 월간 결산 보고서와 분기 검토 자료를 합친 값 ' * 12, True), ('https://example.com/' + 'x' * 400, True)):
            with self.subTest(chars=len(src)):
                lines = wrap_text(src, 716, 11)
                self.assertTrue(1 <= len(lines) <= 3)
                self.assertTrue(all(text_width(ln, 11) <= 716 for ln in lines))
                self.assertEqual(lines[-1].endswith('…'), cut)
                if not cut:
                    self.assertEqual(' '.join(lines).split(), src.split())   # nothing lost when it fits

if __name__ == '__main__':
    unittest.main()
