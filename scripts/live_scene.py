"""Assemble a live (inline JavaScript + SVG) Confluence HTML-macro fragment.

Layers (see references/live-runtime.md):
  model (Python, deterministic)  ->  data JSON
  scene + grammars + kit (JS, pure string renderers, no DOM)
  runtime (JS, browser clock/controls)  ->  one self-contained <section>

The static fallback inside the macro is produced by running the *same* JS scene code
in Node at the final model time (at 720 px and, for phones, 360 px), so print/export/no-JS
output is not a second implementation. Node is a build-time requirement for live cases only.
"""
from __future__ import annotations
import html, json, re, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'visuals/live'
MARK = '/*ca-live-runtime v1*/'
CORE_FILES = ['kit.js', 'grammars/flow-queue.js', 'grammars/time-panels.js']
STATIC_WIDTH = 720
NARROW_WIDTH = 360   # second static scene, shown without JavaScript on phone-width screens


def core_js(scene: str) -> str:
    path = LIVE / 'scenes' / f'{scene}.js'
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', scene) or not path.is_file():
        raise ValueError(f'Unknown live scene: {scene}')
    return '\n'.join((LIVE / f).read_text(encoding='utf-8') for f in CORE_FILES + [f'scenes/{scene}.js'])


def json_for_script(data: dict) -> str:
    # Keep data inert inside <script>: no closing tags, comments or line separators.
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def node_static(data: dict, width: int = STATIC_WIDTH) -> dict:
    node = shutil.which('node')
    if not node:
        raise ValueError('Live cases need Node.js at build time for the static fallback')
    program = core_js(data['scene']) + '\n' + (
        'var D=JSON.parse(require("fs").readFileSync(0,"utf8"));'
        'var sc=CA_SCENES[D.scene](D,CA_KIT,CA_GRAMMARS),g=sc.geom(%d);'
        'process.stdout.write(JSON.stringify({svg:sc.draw(sc.end,g),H:g.H,stats:sc.stats(sc.end)}));' % width)
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / 'static.js'
        script.write_text(program, encoding='utf-8')
        done = subprocess.run([node, str(script)], input=json.dumps(data), capture_output=True,
                              text=True, timeout=60)
    if done.returncode:
        raise ValueError('Static render failed: ' + done.stderr.strip()[-400:])
    return json.loads(done.stdout)


FONT_STACK = 'Pretendard, "Pretendard Variable", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", "Noto Sans CJK KR", sans-serif'


def text_width(s: str, fs: float) -> float:
    """Same conservative estimate as the kit's K.tw (Hangul 1em, digits/Latin 0.62em)."""
    return fs * sum(1.0 if ord(ch) >= 0x1100 else 0.3 if ch == ' ' else 0.36 if ch in '.,·:()/' else 0.62 for ch in s)


def wrap_text(s: str, max_px: float, fs: float, max_lines: int = 3) -> list[str]:
    """Greedy wrap at spaces (characters when one word is too long); the last line ends in …"""
    lines, cur = [], ''
    for word in s.split():
        while word:
            cand = (cur + ' ' + word) if cur else word
            if text_width(cand, fs) <= max_px:
                cur, word = cand, ''
            elif cur:
                lines.append(cur); cur = ''
            else:   # a single word wider than the line: break it
                n = len(word)
                while n > 1 and text_width(word[:n], fs) > max_px:
                    n -= 1
                lines.append(word[:n]); word = word[n:]
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and text_width(last + '…', fs) > max_px:
            last = last[:-1]
        lines = lines[:max_lines - 1] + [last.rstrip() + '…']
    return lines


def figure_svg(data: dict, width: int = STATIC_WIDTH, footer: str = '') -> str:
    """Standalone SVG of the final scene (same scene code) for documents that cannot embed
    HTML: slides, word processors, wikis. White background, system Korean font stack, and a
    provenance footer so an exported image never loses whether its numbers are real."""
    st = node_static(data, width)
    lines = wrap_text(footer, width - 4, 11) if footer else []
    h = st['H'] + 16 + (8 + 15 * len(lines) if lines else 0)
    foot = ''.join('<text x="2" y="%g" font-size="11" fill="#697077">%s</text>' % (h - 6 - 15 * (len(lines) - 1 - i), html.escape(ln))
                   for i, ln in enumerate(lines))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %g" width="%d" height="%g" '
            'font-family=\'%s\' style="font-variant-numeric:tabular-nums">' % (width, h, width, h, FONT_STACK)
            + '<rect width="100%%" height="100%%" fill="#fff"/><g transform="translate(0,8)">' + st['svg'] + '</g>' + foot + '</svg>')


def stats_html(stats: dict) -> str:
    if not stats.get('left') and not stats.get('right'):
        return ''   # empty -> the status line collapses (static figures)
    def b(value, hot):
        return '<b' + (' class="hot"' if hot else '') + '>' + html.escape(str(value)) + '</b>'
    out = '<span class="grp">' + ''.join('<span>' + html.escape(a) + b(v, hot) + html.escape(u) + '</span>'
                                         for a, v, u, hot in stats['left']) + '</span>'
    r = stats.get('right')
    if not r:
        return out
    return out + '<span>' + html.escape(r[0]) + b(r[1], r[4]) + html.escape(r[2]) + b(r[3], r[4]) + '</span>'


def assemble_live(case_id: str, prefix: str, speed: float, data: dict, aria: str, notes: str,
                  table: tuple[list[str], list[list]], live: bool = True) -> str:
    """One self-contained <section>. live=False gives a static figure: same scene code rendered
    once in Node (720 px and 360 px), no script, no controls."""
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,40}', prefix):
        raise ValueError('Invalid prefix')
    static = node_static(data)
    narrow = node_static(data, NARROW_WIDTH)
    final_caption = data['captions'][-1]
    head, rows = table
    table_html = ('<table><thead><tr>' + ''.join('<th scope="col">' + html.escape(h) + '</th>' for h in head) +
                  '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + html.escape(str(c)) + '</td>' for c in row) + '</tr>'
                                                  for row in rows) + '</tbody></table>')
    runtime = (LIVE / 'runtime.js').read_text(encoding='utf-8')
    script = MARK + '\n(function(){"use strict";\n' + core_js(data['scene']) + '\n' + \
        runtime.replace('%%PREFIX%%', prefix).replace('%%DATA%%', json_for_script(data)) + '\n})();'
    if re.search(r'</script|<!--', script, re.I):
        raise ValueError('Script body must not contain a script end tag or HTML comment')
    values = {
        'PREFIX': prefix, 'CASE': case_id, 'SPEED': f'{speed:g}', 'W': str(STATIC_WIDTH), 'H': f"{static['H']:g}",
        'STATIC_SVG': static['svg'], 'STATS': stats_html(static['stats']),
        'WN': str(NARROW_WIDTH), 'HN': f"{narrow['H']:g}", 'STATIC_SVG_N': narrow['svg'],
        'CAPTION': '<span class="n">' + html.escape(final_caption[1]) + '</span>' + html.escape(final_caption[2]),
        'ARIA': html.escape(aria, quote=True), 'NOTES': html.escape(notes), 'TABLE': table_html,
    }
    out = (LIVE / 'shell.html').read_text(encoding='utf-8')
    if not live:
        ctl = re.search(r'\n<div class="ca-live-ctl" data-ca-controls>.*?</div>', out)
        out = out.replace(ctl[0], '').replace('<script>%%SCRIPT%%</script>\n', '').replace('data-ca-runtime="live"', 'data-ca-runtime="static"')
        script = ''
    for key, value in values.items():
        out = out.replace('%%' + key + '%%', value)
    out = out.replace('%%SCRIPT%%', script)   # last: data must not be re-substituted
    if re.search(r'%%[A-Z_]+%%', out.replace(script, '') if script else out):
        raise ValueError('Unresolved live template token')
    return out
