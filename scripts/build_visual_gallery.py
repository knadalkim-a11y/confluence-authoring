#!/usr/bin/env python3
"""Build every spec in a folder and write one review page (index.html) that embeds each macro.

  python scripts/build_visual_gallery.py examples/visuals --out dist/visuals [--check]

For human review of the spec path's output side by side; nothing is published.
"""
from __future__ import annotations
import argparse, html, json, subprocess, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('specs', type=Path); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--check', action='store_true'); a = ap.parse_args()
    here = Path(__file__).resolve().parent; cards = []; ok = True
    for spec in sorted(a.specs.glob('*.json')):
        out = a.out / spec.stem
        r = subprocess.run([sys.executable, str(here / 'build_visual.py'), str(spec), '--out', str(out)] + (['--check'] if a.check else []), capture_output=True, text=True)
        ok &= r.returncode == 0
        s = json.loads(spec.read_text(encoding='utf-8')); rep = json.loads((out / 'report.json').read_text(encoding='utf-8')) if (out / 'report.json').exists() else {}
        gate = rep.get('gates', {}).get('result', 'not run') if rep else 'build failed'
        macro = (out / 'macro.html').read_text(encoding='utf-8') if (out / 'macro.html').exists() else '<p>build failed</p>'
        cards.append(f'<section class="card"><h2>{html.escape(s.get("title", spec.stem))}</h2><p class="meta">{spec.name} · {s.get("kind")} · '
                     f'{rep.get("mode", "?")} · gates: {gate}</p>{macro}</section>')
        print(('PASS' if r.returncode == 0 else 'FAIL'), spec.name, (r.stderr.strip().splitlines() or [''])[-1][:160])
    page = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Document visuals</title><style>body{margin:0;background:#f1f3f5;font:14px/1.6 -apple-system,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;color:#343a40}'
            'main{max-width:760px;margin:0 auto;padding:16px}.card{background:#fff;border-radius:12px;padding:12px 20px 8px;margin:16px 0}'
            'h1{font-size:20px}h2{font-size:16px;margin:4px 0}.meta{color:#697077;font-size:12px;margin:0 0 4px}</style></head><body><main>'
            '<h1>Document visuals built from specs</h1><p class="meta">Each block is the exact macro.html built from the spec named under its title.</p>'
            + ''.join(cards) + '</main></body></html>')
    (a.out / 'index.html').write_text(page, encoding='utf-8')
    print('PASS' if ok else 'FAIL', a.out / 'index.html')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
