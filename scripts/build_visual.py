#!/usr/bin/env python3
"""Build one document visual from a JSON spec: validate, model, assemble, lint, optionally gate.

  python scripts/build_visual.py spec.json --out dist/visuals/<name> [--check] [--prefix ca-x]

Writes macro.html (paste into a Confluence HTML macro), preview.html (standalone page),
figure.svg (+ figure.png when a browser is available) for documents that cannot embed HTML,
report.json and, with --check, browser-gate screenshots under shots/.
Exit code 0 = built and checked (or check not requested), 1 = spec/lint/gate failure,
2 = built but the browser gates could not run (say so when you report the visual).
See references/visual-specs.md.
"""
from __future__ import annotations
import argparse, json, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from visual_spec import build, SpecError
from live_scene import assemble_live, figure_svg, STATIC_WIDTH, document
from validate_html_macro import validate


def make(spec, prefix=None, speed=1.25, phone=False):
    info = build(spec)
    prefix = prefix or 'ca-' + uuid.uuid4().hex[:12]
    frag = assemble_live(spec['kind'], prefix, speed, info['data'], info['aria'], info['notes'], info['table'], live=info['live'], phone=phone)
    return frag, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec', type=Path); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--prefix')
    ap.add_argument('--check', action='store_true', help='run browser quality gates (needs Playwright + Chromium)')
    ap.add_argument('--browser', help='Chromium executable (default: Playwright bundled)')
    ap.add_argument('--font', help='force a font family during the gates (e.g. NanumGothic) to test other metrics')
    ap.add_argument('--phone', action='store_true', help='also build the 360 px phone scene and check phone widths (off: read on monitors)')
    a = ap.parse_args()
    try:
        spec = json.loads(a.spec.read_text(encoding='utf-8'))
        frag, info = make(spec, a.prefix, phone=a.phone)
    except (SpecError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print('FAIL spec:', e, file=sys.stderr); return 1
    errors = validate(frag)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'macro.html').write_text(frag, encoding='utf-8')
    (a.out / 'preview.html').write_text(document(frag, info['title']), encoding='utf-8')
    dk = info['data']['labels'].get('data_kind', ''); src = spec.get('source', '')
    svg = figure_svg(info['data'], footer=f'출처: {src}' + ('' if dk in src else f' · {dk}'))
    (a.out / 'figure.svg').write_text(svg, encoding='utf-8')
    from visual_gates import caption_report
    report = dict(kind=spec['kind'], mode='live' if info['live'] else 'static', bytes=len(frag.encode()), lint=errors or 'PASS',
                  captions=caption_report(info['data'], info['checks']['end']) if info['live'] else None)
    try:   # clutter numbers (scripts/figure_metrics.py) and the layout decisions the scene made, at the column width
        from figure_metrics import metrics
        from live_scene import node_static
        st = {w: node_static(info['data'], w) for w in (715, 600)}
        report['clutter'] = {w: metrics(st[w]['svg']) for w in st}
        report['layout'] = st[715].get('notes') or []
        # correspondence: which part each captioned step (caption or list row) is about; the engine lights it up
        # while the step is current. Read it to check that every row names the part you meant.
        if info['data'].get('marks'):
            report['correspondence'] = [dict(step=m['mark'], part=m['target']) for m in info['data']['marks']]
        for n in report['layout']:
            print('layout:', n, file=sys.stderr)
    except Exception as e:   # no Node: the figure is still built
        report['clutter'] = f'not measured ({str(e)[:80]})'
    if errors:
        print('FAIL lint:', '; '.join(errors), file=sys.stderr)
    unchecked = None
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sync_playwright = None
    if sync_playwright is None:
        unchecked = 'Playwright is not installed (pip install playwright; a Chromium binary is needed too)'
    elif not errors:
        from visual_gates import figure_problems
        fig = []
        try:
            with sync_playwright() as pw:   # PNG of the standalone figure, at 2x for slides/documents
                br = pw.chromium.launch(executable_path=a.browser, headless=True, args=['--no-sandbox'])
                pg = br.new_page(device_scale_factor=2, viewport={'width': STATIC_WIDTH, 'height': 1000})
                pg.set_content('<body style="margin:0">' + svg + '</body>'); fig = figure_problems(pg)
                pg.locator('svg').first.screenshot(path=str(a.out / 'figure.png'))
                if a.font:   # the same checks under the forced font; the PNG keeps the normal stack
                    pg.set_content(f'<head><style>svg *{{font-family:"{a.font}"!important}}</style></head><body style="margin:0">' + svg + '</body>')
                    fig += [p + f' ({a.font})' for p in figure_problems(pg)]
                br.close()
        except Exception as e:   # no browser binary: the HTML/SVG outputs are still valid
            unchecked = f'Chromium could not start ({str(e).splitlines()[0][:120]})'
        report['figure'] = fig or 'PASS'
        for p in fig:
            print(('FAIL gate:' if a.check else 'WARN'), p, file=sys.stderr)
    if a.check and not errors and not unchecked:
        from visual_gates import run
        import shutil
        shutil.rmtree(a.out / 'shots', ignore_errors=True)   # never review a stale screenshot
        rec = run(frag, info['checks'], info['data'], a.out / 'shots', a.spec.stem, a.browser, font=a.font, phone=a.phone)
        if report.get('figure', 'PASS') != 'PASS':   # the exported SVG/PNG is part of the deliverable
            rec['failures'] = list(rec['failures']) + report['figure']; rec['result'] = 'FAIL'
        report['gates'] = rec
        for f in rec['failures']:
            print('FAIL gate:', f, file=sys.stderr)
    elif a.check and unchecked:
        report['gates'] = dict(result='NOT RUN', reason=unchecked)
        print('WARN gates not run:', unchecked, file=sys.stderr)
    (a.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    if errors or (a.check and report['gates']['result'] == 'FAIL'):
        status, code = 'FAIL', 1
    elif a.check and report['gates']['result'] == 'NOT RUN':
        status, code = 'BUILT (unchecked)', 2
    else:
        status, code = 'PASS', 0
    print(status, report['mode'], a.out / 'macro.html', f"{report['bytes'] / 1024:.0f} KB")
    return code


if __name__ == '__main__':
    raise SystemExit(main())
