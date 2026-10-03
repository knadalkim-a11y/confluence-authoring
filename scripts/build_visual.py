#!/usr/bin/env python3
"""Build one document visual from a JSON spec: validate, model, assemble, lint, optionally gate.

  python scripts/build_visual.py spec.json --out dist/visuals/<name> [--check] [--prefix ca-x]

Writes macro.html (paste into a Confluence HTML macro), preview.html, report.json and, with
--check, browser-gate screenshots under shots/. Exit code 1 on any spec, lint or gate failure.
See references/visual-specs.md.
"""
from __future__ import annotations
import argparse, json, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from visual_spec import build, SpecError
from live_scene import assemble_live
from reference_scene import document
from validate_html_macro import validate


def make(spec, prefix=None, speed=1.25):
    info = build(spec)
    prefix = prefix or 'ca-' + uuid.uuid4().hex[:12]
    frag = assemble_live(spec['kind'], prefix, speed, info['data'], info['aria'], info['notes'], info['table'], live=info['live'])
    return frag, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec', type=Path); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--prefix')
    ap.add_argument('--check', action='store_true', help='run browser quality gates (needs Playwright + Chromium)')
    ap.add_argument('--browser', help='Chromium executable (default: Playwright bundled)')
    a = ap.parse_args()
    try:
        spec = json.loads(a.spec.read_text(encoding='utf-8'))
        frag, info = make(spec, a.prefix)
    except (SpecError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print('FAIL spec:', e, file=sys.stderr); return 1
    errors = validate(frag)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'macro.html').write_text(frag, encoding='utf-8')
    (a.out / 'preview.html').write_text(document(frag, info['title']), encoding='utf-8')
    from visual_gates import caption_report
    report = dict(kind=spec['kind'], mode='live' if info['live'] else 'static', bytes=len(frag.encode()), lint=errors or 'PASS',
                  captions=caption_report(info['data'], info['checks']['end']) if info['live'] else None)
    if errors:
        print('FAIL lint:', '; '.join(errors), file=sys.stderr)
    if a.check and not errors:
        from visual_gates import run
        import shutil
        shutil.rmtree(a.out / 'shots', ignore_errors=True)   # never review a stale screenshot
        rec = run(frag, info['checks'], info['data'], a.out / 'shots', a.spec.stem, a.browser)
        report['gates'] = rec
        for f in rec['failures']:
            print('FAIL gate:', f, file=sys.stderr)
    (a.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    ok = not errors and (not a.check or report['gates']['result'] == 'PASS')
    print(('PASS' if ok else 'FAIL'), report['mode'], a.out / 'macro.html', f"{report['bytes'] / 1024:.0f} KB")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
