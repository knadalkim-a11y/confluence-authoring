#!/usr/bin/env python3
"""Clutter metrics for built figures, from the final static scene (the same JS scene run in Node).

  python scripts/figure_metrics.py spec.json [...] [--root <repo>] [--widths 715,360] [--json out.json]

The browser gates catch defects (overlap, clipping, a line through a box); they say nothing about how busy a
picture is. These numbers do: connectors drawn with K.wire, their segments and bends, crossings between two
different connectors, and total connector length (px). Use them to compare a change against a baseline built
from the previous revision (--root points at a checkout of it): a layout or routing change that makes figures
busier should not be accepted on "gates pass" alone. Lower is calmer; the numbers do not judge meaning.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path


def metrics(svg: str) -> dict:
    wires = []
    for m in re.finditer(r'<polyline[^>]*data-wire="1"[^>]*points="([^"]+)"', svg):
        q = [float(x) for x in m.group(1).split()]
        pts = list(zip(q[::2], q[1::2]))
        pts = [p for i, p in enumerate(pts) if i == 0 or abs(p[0] - pts[i - 1][0]) + abs(p[1] - pts[i - 1][1]) > 0.5]
        if len(pts) >= 2:
            wires.append(pts)
    segs = [(k, a, b) for k, w in enumerate(wires) for a, b in zip(w, w[1:])]
    bends = sum(len(w) - 2 for w in wires)
    length = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for _, a, b in segs)

    def cross(s, t):   # a horizontal and a vertical segment of two connectors meet away from their ends
        (_, a, b), (_, c, d) = s, t
        h1, h2 = abs(a[1] - b[1]) < .5, abs(c[1] - d[1]) < .5
        if h1 == h2:
            return False
        (ha, hb), (va, vb) = ((a, b), (c, d)) if h1 else ((c, d), (a, b))
        x, y = va[0], ha[1]
        return min(ha[0], hb[0]) + 2 < x < max(ha[0], hb[0]) - 2 and min(va[1], vb[1]) + 2 < y < max(va[1], vb[1]) - 2
    crossings = sum(1 for i in range(len(segs)) for j in range(i + 1, len(segs)) if segs[i][0] != segs[j][0] and cross(segs[i], segs[j]))
    return dict(wires=len(wires), segments=len(segs), bends=bends, crossings=crossings, length=round(length))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('specs', nargs='+', type=Path)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='repository whose scripts build the figures')
    ap.add_argument('--widths', default='715,360')
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    sys.path.insert(0, str(a.root / 'scripts'))
    from visual_spec import build
    from live_scene import node_static
    out = {}
    for f in a.specs:
        data = build(json.loads(f.read_text(encoding='utf-8')))['data']
        out[f.stem] = {w: metrics(node_static(data, int(w))['svg']) for w in a.widths.split(',')}
        print(f.stem, json.dumps(out[f.stem]))
    if a.json:
        a.json.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
