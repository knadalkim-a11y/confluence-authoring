"""Live-runtime browser quality gates for the monitoring live cases (JavaScript enabled).

Runs the shared gate runner (scripts/visual_gates.py) with each case's model expectations
from monitoring_cases.live_checks(), then checks that the gallery executes the mounted
macro. Gates do not judge aesthetics; screenshots are written for review.
Not a Confluence test: target-page script execution and PDF export remain unverified.
"""
from __future__ import annotations
from pathlib import Path
import argparse, datetime, json, sys
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from playwright.sync_api import sync_playwright
from monitoring_cases import build_case, live_checks, LIVE_BUILDERS
from reference_scene import document
from visual_gates import run

ap = argparse.ArgumentParser(); ap.add_argument('--browser'); ap.add_argument('--output', type=Path, default=ROOT / 'dist/live')
opt = ap.parse_args(); OUT = opt.output; SHOTS = OUT / 'screenshots'; SHOTS.mkdir(parents=True, exist_ok=True)
CASES = [c for c in json.loads((ROOT / 'examples/monitoring-cases.json').read_text())['cases'] if c.get('runtime') == 'live']
report = {'confluence_verified': False, 'tested_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'cases': []}
failed = False
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=opt.browser, headless=True, args=['--no-sandbox'])
    report['browser'] = browser.version
    for c in CASES:
        frag, _ = build_case(c, 'ca-live-b', speed=1.25)
        data = LIVE_BUILDERS[c['id']](c['params'])[0]
        (OUT / c['id']).mkdir(parents=True, exist_ok=True)
        (OUT / c['id'] / 'macro.html').write_text(frag, encoding='utf8'); (OUT / c['id'] / 'preview.html').write_text(document(frag, c['title']), encoding='utf8')
        rec = run(frag, live_checks(c['id'], c['params']), data, SHOTS, c['id'], browser=browser)
        # Gallery mounts and runs the exact macro (innerHTML never executes scripts; the gallery re-creates them).
        gallery = ROOT / 'dist/monitoring-suite/gallery.html'
        if gallery.exists():
            ctx = browser.new_context(viewport={'width': 1450, 'height': 1050}); gp = ctx.new_page(); ge = []; gp.on('pageerror', lambda e: ge.append(str(e)))
            gp.set_content(gallery.read_text(encoding='utf8')); gp.wait_for_timeout(150)
            ids = [x['id'] for x in json.loads((ROOT / 'dist/monitoring-suite/manifest.json').read_text())['cases']]
            gp.locator('#lab-list button').nth(ids.index(c['id'])).click(); gp.wait_for_timeout(900)
            end = rec.get('checks', {}) and live_checks(c['id'], c['params'])['end']
            ok = gp.locator('#lab-preview [data-ca-live-bound]').count() == 1 and 0 < float(gp.get_attribute('#lab-preview [data-ca-prefix]', 'data-ca-t')) < end and not ge
            if not ok: rec['failures'].append('gallery does not execute the mounted live macro')
            rec['checks']['gallery_executes_live_macro'] = ok; ctx.close()
        rec['result'] = 'FAIL' if rec['failures'] else 'PASS'; failed |= bool(rec['failures'])
        report['cases'].append(rec); print(rec['result'], c['id'], json.dumps(rec['checks'], ensure_ascii=False)[:300])
        for f in rec['failures']: print('   FAIL:', f)
    browser.close()
report['result'] = 'FAIL' if failed else 'PASS'
(OUT / 'live-browser-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
raise SystemExit(1 if failed else 0)
