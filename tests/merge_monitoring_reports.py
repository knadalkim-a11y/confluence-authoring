"""Merge actual browser shards only if they cover every current artifact exactly once."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/monitoring-suite'

def main():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
    paths=[OUT/'browser-cases-0-10.json',OUT/'browser-cases-10-9.json',OUT/'browser-extra.json']
    reports=[json.loads(p.read_text(encoding='utf8')) for p in paths]
    test_hash=hashlib.sha256((ROOT/'tests/browser_monitoring.py').read_bytes()).hexdigest()
    if any(r.get('result')!='PASS' or r.get('test_sha256')!=test_hash for r in reports):
        raise ValueError('Failed or stale browser report')
    cases=reports[0]['cases']+reports[1]['cases']
    expected={c['id']:c['sha256'] for c in manifest['cases']}
    if len(cases)!=len(expected) or len({c['id'] for c in cases})!=len(cases):
        raise ValueError('Duplicate or incomplete case coverage')
    if any(expected.get(c['id'])!=c['sha256'] for c in cases):
        raise ValueError('Rendered artifact changed after testing')
    checks=reports[-1]['checks']
    required=['independent_instances','keyboard_visible_focus','event_loop_actual_rotation_holds',
              'eight_worker_slots_at_model_5s','gallery_all_cases_filter_search_exact_code_and_single_preview']
    if not all(checks.get(k) is True for k in required):raise ValueError('Extra checks incomplete')
    result=dict(reports[-1]);result.update(cases=cases,case_count=len(cases),
        execution='Two complete case shards (10+9) and independent extras; same test SHA and artifact SHA256.',
        artifact_hash_parity_verified=True,source_reports=[p.name for p in paths])
    (OUT/'browser-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS:',len(cases),'cases + extra checks')
if __name__=='__main__':main()
