"""Offline motion rendering. Python 3.10+, standard library only.

All user strings are escaped. Only renderer-produced SVG/HTML can enter markup slots.
Numerical geometry and summary labels are derived from the same validated data.
"""
from __future__ import annotations
import sys
sys.path.insert(1, str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'scripts'))   # the product scripts (model, live_scene, visual_spec)
import html
import json
import math
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"{{([A-Z][A-Z0-9_]*)}}")
PREFIX = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,40}\Z")
STATES = {"done": ("#eff8f2", "#afd1be", "완료"), "waiting": ("#fff6e8", "#d4b17a", "대기"), "error": ("#fff0f2", "#daa4ac", "실패"), "neutral": ("#f7f9fc", "#dce5ef", "상태 미지정")}
COMMON = {"title", "description", "caption", "provenance", "data_mode", "duration", "repeat"}
FIELDS = {
    "line-reveal": {"series", "unit", "x_label", "change_index"},
    "threshold-cross": {"series", "unit", "x_label", "threshold"},
    "recovery": {"series", "unit", "x_label", "incident_index", "recovery_index"},
    "distribution-percentile": {"values", "counts", "unit"},
    "sequential-flow": {"steps"}, "before-after": {"before", "after"},
    "parallel-flow": {"start", "left", "right", "join"},
    "branch-flow": {"decision", "routes", "selected"},
    "approval-gate": {"steps", "reviewer", "gate"},
    "retry-loop": {"attempts"},
    "request-response": {"client", "server", "request", "response"},
    "queue-buildup": {"arrivals", "capacity", "initial"},
    "failure-propagation": {"components"},
}


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(value: object, name: str, maximum: int = 300) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
        raise ValueError(f"{name}: nonempty text up to {maximum} characters required")
    return value


def number(value: object, name: str, lo: float = 0, hi: float = 1e9, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{name}: finite number in [{lo}, {hi}] required")
    if integer and int(value) != value:
        raise ValueError(f"{name}: integer required")
    return value


def array(value: object, name: str, lo: int = 2, hi: int = 8) -> list:
    if not isinstance(value, list) or not lo <= len(value) <= hi:
        raise ValueError(f"{name}: list of {lo}..{hi} items required")
    return value


def fmt(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".") if value != int(value) else f"{int(value):,}"


def substitute(source: str, values: dict[str, str]) -> str:
    missing = set(TOKEN.findall(source)) - values.keys()
    if missing:
        raise ValueError("Missing template slots: " + ", ".join(sorted(missing)))
    return TOKEN.sub(lambda m: values[m[1]], source)


def weighted_stats(values: list[float], counts: list[int]) -> tuple[float, float]:
    total = sum(counts)
    if total <= 0:
        raise ValueError("At least one observation is required")
    mean = sum(v * n for v, n in zip(values, counts)) / total
    rank = math.ceil(.95 * total)
    cumulative = 0
    for value, count in sorted(zip(values, counts)):
        cumulative += count
        if cumulative >= rank:
            return mean, value
    raise AssertionError("unreachable percentile")


def queue_states(arrivals: list[int], capacity: list[int], initial: int) -> list[tuple[int, int]]:
    result = []
    backlog = initial
    for incoming, limit in zip(arrivals, capacity):
        served = min(backlog + incoming, limit)
        backlog += incoming - served
        result.append((served, backlog))
    return result


class Scene:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.rules: list[str] = []
        self.table = ""

    def animate(self, frames: str, final: str) -> str:
        key = f"k{len(self.rules)}"
        name = self.prefix + "-" + key
        self.rules.append(f".{self.prefix} .{key}{{--a:{name}-a;--b:{name}-b;{final}}}\n@keyframes {name}-a{{{frames}}}\n@keyframes {name}-b{{{frames}}}")
        return f"ca-anim {key}"

    def reveal(self, at: float) -> str:
        return self.animate(f"0%,{at:.2f}%{{opacity:0}}{at+5:.2f}%,100%{{opacity:1}}", "opacity:1")

    def node(self, item: object, index: int, start: float, end: float) -> str:
        if isinstance(item, str):
            item = {"title": item, "detail": "", "state": "neutral"}
        if not isinstance(item, dict) or set(item) - {"title", "detail", "state"}:
            raise ValueError("Node requires title and optional detail/state")
        title = text(item.get("title"), "node.title", 70)
        detail = item.get("detail", "")
        if not isinstance(detail, str) or len(detail) > 200:
            raise ValueError("node.detail: text up to 200 characters required")
        state = item.get("state", "neutral")
        if not isinstance(state, str) or state not in STATES:
            raise ValueError("Unsupported node state")
        bg, border, status = STATES[state]
        cls = self.animate(f"0%,{start:.2f}%{{background:#f7f9fc;border-color:#dce5ef}}{start+3:.2f}%,{end-3:.2f}%{{background:#edf4ff;border-color:#7ba0d5}}{end:.2f}%,100%{{background:{bg};border-color:{border}}}", f"background:{bg};border-color:{border}")
        # This explicitly describes the final scenario, not a live execution status.
        return f'<div class="ca-node {cls}"><div class="ca-tag">{index:02d}</div><h4>{escape(title)}</h4><p>{escape(detail)}</p><span class="ca-status">최종 상태: {status}</span></div>'

    def flow(self, items: object, start: float = 5, end: float = 78) -> str:
        nodes = array(items, "steps", 1, 6)
        width = (end - start) / len(nodes)
        return '<div class="ca-grid">' + ''.join(self.node(v, i+1, start+i*width, start+(i+1)*width) for i, v in enumerate(nodes)) + '</div>'

    def data_table(self, headers: list[str], rows: list[list[object]]) -> None:
        head = ''.join(f'<th scope="col">{escape(x)}</th>' for x in headers)
        body = ''.join('<tr>' + ''.join(f'<td>{escape(x)}</td>' for x in row) + '</tr>' for row in rows)
        self.table = f'<details><summary>데이터 / 전체 단계 보기</summary><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></details>'

    def svg(self, content: str, title: str, height: int = 260) -> str:
        return f'<svg class="ca-chart" viewBox="0 0 500 {height}" role="img" aria-labelledby="{self.prefix}-svg-title"><title id="{self.prefix}-svg-title">{escape(title)}</title>{content}</svg>'


def chart(scene: Scene, pattern: str, data: dict) -> dict[str, str]:
    series = array(data.get("series"), "series", 3, 40)
    for x in series:
        number(x, "series item")
    unit = text(data.get("unit"), "unit", 30)
    x_label = text(data.get("x_label"), "x_label", 80)
    threshold = number(data.get("threshold"), "threshold") if pattern == "threshold-cross" else 0
    limit = max(max(series), threshold, 1) * 1.2
    xx = lambda i: 54 + i * 416 / (len(series)-1)
    yy = lambda v: 208 - v / limit * 160
    grid = ''.join(f'<line class="ca-axis" x1="54" x2="470" y1="{yy(limit*i/3):.2f}" y2="{yy(limit*i/3):.2f}"/><text x="46" y="{yy(limit*i/3)+5:.2f}" text-anchor="end">{escape(fmt(limit*i/3))}</text>' for i in range(4))
    points = ' '.join(f'{xx(i):.2f},{yy(v):.2f}' for i, v in enumerate(series))
    lengths = [0.0]
    for i in range(1, len(series)):
        lengths.append(lengths[-1] + math.hypot(xx(i)-xx(i-1), yy(series[i])-yy(series[i-1])))
    reveal_at = lambda i: 5 + 73 * lengths[i] / lengths[-1]
    draw = scene.animate('0%,5%{stroke-dashoffset:1}78%,100%{stroke-dashoffset:0}', 'stroke-dashoffset:0')
    lines = f'<polyline class="ca-trace {draw}" pathLength="1" points="{points}"/>'
    notes = ''
    if pattern == "threshold-cross":
        crossing = next((i for i, v in enumerate(series) if v > threshold), None)
        notes = f'<line x1="54" x2="470" y1="{yy(threshold):.2f}" y2="{yy(threshold):.2f}" stroke="#ad7030" stroke-dasharray="5 5"/>'
        marker = "임계치 초과 없음" if crossing is None else f"첫 초과: 관측 {crossing+1}"
        if crossing is not None:
            cls = scene.reveal(reveal_at(crossing))
            notes += f'<circle class="{cls}" cx="{xx(crossing):.2f}" cy="{yy(series[crossing]):.2f}" r="6" fill="#ad7030"/>'
        metric = f"기준 {fmt(threshold)} {unit} · {marker}"
    elif pattern == "recovery":
        incident = int(number(data.get("incident_index"), "incident_index", 0, len(series)-2, True))
        recovery = int(number(data.get("recovery_index"), "recovery_index", incident+1, len(series)-1, True))
        for i, color in [(incident, '#ad3947'), (recovery, '#277657')]:
            cls = scene.reveal(reveal_at(i))
            notes += f'<line class="{cls}" x1="{xx(i):.2f}" x2="{xx(i):.2f}" y1="35" y2="208" stroke="{color}" stroke-dasharray="4 4"/>'
        metric = f"입력된 발생 지점: {incident+1} · 회복 지점: {recovery+1} (원인·회복 여부 자동 판정 아님)"
    else:
        i = int(number(data.get("change_index"), "change_index", 0, len(series)-1, True))
        cls = scene.reveal(reveal_at(i))
        notes = f'<line class="{cls}" x1="{xx(i):.2f}" x2="{xx(i):.2f}" y1="35" y2="208" stroke="#ad7030" stroke-dasharray="4 4"/>'
        metric = f"시작 {fmt(series[0])} → 마지막 {fmt(series[-1])} {unit} · 강조 지점 {i+1}"
    labels = f'<text x="54" y="242">1</text><text x="470" y="242" text-anchor="end">{len(series)}</text>'
    scene.data_table([x_label, unit], [[i+1, fmt(v)] for i, v in enumerate(series)])
    return {"CHART": scene.svg(grid+lines+notes+labels, data['title']), "METRICS": escape(metric), "AXIS_LABEL": escape(f"{x_label} · 단위 {unit} · 동일 간격 관측")}


def distribution(scene: Scene, data: dict) -> dict[str, str]:
    values = array(data.get('values'), 'values', 2, 14)
    counts = array(data.get('counts'), 'counts', len(values), len(values))
    for value in values:
        number(value, 'value')
    if sorted(values) != values or len(set(values)) != len(values):
        raise ValueError('values must be unique and ascending')
    for count in counts:
        number(count, 'count', 0, 1000000, True)
    unit = text(data.get('unit'), 'unit', 30)
    mean, p95 = weighted_stats(values, counts)
    upper = max(values[-1]*1.12, 1)
    x = lambda v: 54 + v/upper*416
    width = min(30, min(x(b)-x(a) for a,b in zip(values,values[1:]))*.7)
    max_count = max(counts)
    grow = scene.animate('0%,5%{transform:scaleY(0)}42%,100%{transform:scaleY(1)}', 'transform:scaleY(1)')
    bars = ''.join(f'<rect class="ca-bar {grow}" x="{x(v)-width/2:.2f}" y="{208-c/max_count*135:.2f}" width="{width:.2f}" height="{c/max_count*135:.2f}"/>' for v,c in zip(values,counts))
    for value, at, color, label_y, label in [(mean,46,'#466b9e',32,'평균'),(p95,68,'#7951b0',55,'P95')]:
        cls=scene.reveal(at)
        bars+=f'<g class="{cls}"><line x1="{x(value):.2f}" x2="{x(value):.2f}" y1="{label_y+5}" y2="208" stroke="{color}" stroke-dasharray="4 4"/><text x="{x(value):.2f}" y="{label_y}" text-anchor="middle">{label}</text></g>'
    bars+='<line class="ca-axis" x1="54" x2="470" y1="208" y2="208"/>'
    for v in [0, upper/2, upper]:
        bars+=f'<text x="{x(v):.2f}" y="240" text-anchor="middle">{escape(fmt(v))}</text>'
    scene.data_table([unit, '건수'], [[fmt(v),c] for v,c in zip(values,counts)])
    return {'CHART':scene.svg(bars,data['title']), 'METRICS':escape(f"표본 {sum(counts)}건 · 평균 {fmt(mean)} {unit} · P95 {fmt(p95)} {unit}"), 'AXIS_LABEL':escape(f"가로축 {unit} · 막대 높이 건수 (최대 {max_count}) · P95: nearest-rank")}


def build_scene(scene: Scene, pattern: str, d: dict) -> dict[str, str]:
    if pattern in {'line-reveal','threshold-cross','recovery'}:
        return chart(scene,pattern,d)
    if pattern=='distribution-percentile':
        return distribution(scene,d)
    if pattern=='sequential-flow':
        return {'STEPS':scene.flow(d.get('steps'))}
    if pattern=='before-after':
        return {'BEFORE':scene.flow(d.get('before'),5,42), 'AFTER':scene.flow(d.get('after'),46,82)}
    if pattern=='parallel-flow':
        return {'START':scene.flow([d.get('start')],3,18), 'LEFT':scene.flow(d.get('left'),24,62), 'RIGHT':scene.flow(d.get('right'),24,62), 'JOIN':scene.flow([d.get('join')],68,84)}
    if pattern=='branch-flow':
        routes=array(d.get('routes'),'routes',2,4)
        selected=int(number(d.get('selected'),'selected',0,len(routes)-1,True))
        rendered=[]
        for i,item in enumerate(routes):
            label=text(item,'route',100)
            chosen=i==selected
            cls=scene.reveal(32+i*3) if chosen else ''
            rendered.append(f'<div class="ca-panel {cls}"><div class="ca-tag">경로 {i+1} · {"선택됨" if chosen else "미선택"}</div><h4>{escape(label)}</h4></div>')
        return {'DECISION':escape(text(d.get('decision'),'decision')), 'ROUTES':''.join(rendered)}
    if pattern=='approval-gate':
        gate=text(d.get('gate'),'gate')
        reviewer=text(d.get('reviewer'),'reviewer',100)
        return {'STEPS':scene.flow(d.get('steps'),4,56), 'GATE':scene.flow([{'title':reviewer,'detail':gate,'state':'waiting'}],64,82)}
    if pattern=='retry-loop':
        attempts=array(d.get('attempts'),'attempts',2,5)
        for item in attempts[:-1]:
            if not isinstance(item,dict) or item.get('state')!='error':
                raise ValueError('Every attempt before the last must be error; no retry after success')
        return {'ATTEMPTS':scene.flow(attempts), 'LIMIT':str(len(attempts))}
    if pattern=='request-response':
        values={key.upper():escape(text(d.get(key),key,100)) for key in ['client','server','request','response']}
        a=scene.animate('0%,10%{transform:translateX(0);opacity:0}12%{opacity:1}42%{transform:translateX(380px);opacity:1}44%,100%{transform:translateX(380px);opacity:0}', 'opacity:0;transform:translateX(380px)')
        b=scene.animate('0%,51%{transform:translateX(0);opacity:0}53%{opacity:1}83%{transform:translateX(-380px);opacity:1}85%,100%{transform:translateX(-380px);opacity:0}', 'opacity:0;transform:translateX(-380px)')
        values['CHANNEL']=scene.svg(f'<path d="M55 23 H435 l-8 -5 m8 5 l-8 5 M435 58 H55 l8 -5 m-8 5 l8 5" fill="none" stroke="#91a8c2" stroke-width="2"/><circle class="{a}" cx="55" cy="23" r="5" fill="#326cce"/><circle class="{b}" cx="435" cy="58" r="5" fill="#7951b0"/>','위쪽은 요청, 아래쪽은 역방향 응답',82)
        return values
    if pattern=='queue-buildup':
        arrivals=array(d.get('arrivals'),'arrivals',3,10)
        capacity=array(d.get('capacity'),'capacity',len(arrivals),len(arrivals))
        for v in arrivals+capacity:
            number(v,'arrivals/capacity',0,1000000,True)
        initial=int(number(d.get('initial',0),'initial',0,1000000,True))
        states=queue_states(arrivals,capacity,initial)
        mx=max(1,max(n for _,n in states))
        width=380/len(states)
        bars=''
        for i,(_,n) in enumerate(states):
            cls=scene.reveal(6+i*65/len(states))
            h=n/mx*140
            x=65+i*width
            bars+=f'<g class="{cls}"><rect x="{x:.2f}" y="{205-h:.2f}" width="{width*.6:.2f}" height="{h:.2f}" fill="#bd8850"/><text x="{x+width*.3:.2f}" y="{195-h:.2f}" text-anchor="middle">{n}</text><text x="{x+width*.3:.2f}" y="237" text-anchor="middle">{i+1}</text></g>'
        bars+='<line class="ca-axis" x1="54" x2="470" y1="205" y2="205"/>'
        scene.data_table(['구간','유입','처리 한도','실제 처리','잔여'], [[i+1,a,c,s,n] for i,(a,c,(s,n)) in enumerate(zip(arrivals,capacity,states))])
        return {'CHART':scene.svg(bars,d['title']), 'METRICS':escape(f"초기 대기 {initial} · 마지막 대기 {states[-1][1]} · 누적 처리 {sum(s for s,_ in states)}"), 'AXIS_LABEL':'가로축 구간 · 막대 높이 잔여 대기 건수'}
    if pattern=='failure-propagation':
        return {'COMPONENTS':scene.flow(d.get('components'))}
    raise ValueError('Unknown implemented pattern')


def render(pattern: str, data: dict, prefix: str | None = None) -> str:
    if not isinstance(pattern, str) or pattern not in FIELDS:
        raise ValueError(f'Unknown or planned pattern: {pattern}')
    if not isinstance(data,dict):
        raise ValueError('Input must be an object')
    unknown=set(data)-COMMON-FIELDS[pattern]
    if unknown:
        raise ValueError('Unknown inputs: '+','.join(sorted(unknown)))
    prefix=('ca-'+uuid.uuid4().hex[:12]) if prefix is None else prefix
    if not isinstance(prefix, str) or not PREFIX.fullmatch(prefix):
        raise ValueError('Invalid prefix')
    for field in ['title','description','caption','provenance']:
        text(data.get(field),field,800 if field in {'caption','provenance'} else 300)
    mode=data.get('data_mode')
    labels={'illustrative':'설명용 예시','measured':'측정 자료','proposed':'제안 시나리오'}
    if not isinstance(mode, str) or mode not in labels:
        raise ValueError('Explicit data_mode required: illustrative/measured/proposed')
    duration=number(data.get('duration',14),'duration',8,30)
    repeat=data.get('repeat',1)
    if type(repeat) is not int and repeat!='infinite' or type(repeat) is int and repeat!=1:
        raise ValueError('repeat must be 1 or infinite')
    scene=Scene(prefix)
    values=build_scene(scene,pattern,data)
    body=(ROOT/'visuals/motion'/f'{pattern}.html').read_text(encoding='utf-8')
    scene_html=substitute(body,values)
    style=substitute((ROOT/'visuals/components/player.css').read_text(encoding='utf-8'), {'PREFIX':prefix,'DURATION':str(duration),'REPEAT':str(repeat)})
    values={'PREFIX':prefix,'PATTERN':pattern,'CSS':style,'ANIMATION_CSS':'\n'.join(scene.rules),'SCENE':scene_html,'DURATION':str(duration),'MODE_LABEL':labels[mode],'DATA_TABLE':scene.table}
    values.update({key.upper():escape(data[key]) for key in ['title','description','caption','provenance']})
    result=substitute((ROOT/'visuals/components/player.html').read_text(encoding='utf-8'),values)
    if TOKEN.search(result):
        raise ValueError('Unresolved/reserved token in output')
    return result


def document(fragment: str) -> str:
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Confluence motion preview</title><body style="margin:0;padding:16px">'+fragment+'</body></html>'
