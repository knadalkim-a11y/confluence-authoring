"""Assemble a live (inline JavaScript + SVG) Confluence HTML-macro fragment.

Layers (see references/live-runtime.md):
  model (Python, deterministic)  ->  data JSON
  scene + grammars + kit (JS, pure string renderers, no DOM)
  runtime (JS, browser clock/controls)  ->  one self-contained <section>

The static fallback inside the macro is produced by running the *same* JS scene code
in Node at the final model time, so print/export/no-JS output is not a second
implementation. Node is a build-time requirement for live cases only.
"""
from __future__ import annotations
import html, json, re, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'visuals/live'
MARK = '/*ca-live-runtime v1*/'
CORE_FILES = ['kit.js', 'grammars/flow-queue.js', 'grammars/time-panels.js']
STATIC_WIDTH = 720


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


def stats_html(stats: dict) -> str:
    def b(value, hot):
        return '<b' + (' class="hot"' if hot else '') + '>' + html.escape(str(value)) + '</b>'
    out = '<span class="grp">' + ''.join('<span>' + html.escape(a) + b(v, hot) + html.escape(u) + '</span>'
                                         for a, v, u, hot in stats['left']) + '</span>'
    r = stats.get('right')
    if not r:
        return out
    return out + '<span>' + html.escape(r[0]) + b(r[1], r[4]) + html.escape(r[2]) + b(r[3], r[4]) + '</span>'


def assemble_live(case_id: str, prefix: str, speed: float, data: dict, aria: str, notes: str,
                  table: tuple[list[str], list[list]]) -> str:
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,40}', prefix):
        raise ValueError('Invalid prefix')
    static = node_static(data)
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
        'CAPTION': '<span class="n">' + html.escape(final_caption[1]) + '</span>' + html.escape(final_caption[2]),
        'ARIA': html.escape(aria, quote=True), 'NOTES': html.escape(notes), 'TABLE': table_html,
    }
    out = (LIVE / 'shell.html').read_text(encoding='utf-8')
    for key, value in values.items():
        out = out.replace('%%' + key + '%%', value)
    out = out.replace('%%SCRIPT%%', script)   # last: data must not be re-substituted
    if re.search(r'%%[A-Z_]+%%', out.replace(script, '')):
        raise ValueError('Unresolved live template token')
    return out
