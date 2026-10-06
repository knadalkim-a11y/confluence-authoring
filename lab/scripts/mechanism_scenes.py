"""Mechanism-first reference scenes, independently drawn for the existing CSS player.

Only the cascade routing policy and the synthetic single-thread task schedule are
modelled. Failure times and saturation trajectories are explanatory assumptions.
No live monitoring, Node runtime emulation, or original-source redistribution.
"""
from __future__ import annotations
import heapq
import math
from reference_scene import esc, fmt, piece

BLUE = '#316dca'
TEAL = '#258571'
PURPLE = '#8260bd'
AMBER = '#ae771f'
RED = '#bf465b'
INK = '#203d5c'
MUTED = '#6c8299'
LINE = '#c5d3e3'


def text(x, y, value, size=17, color=INK, weight=400, anchor='middle', extra=''):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'style="font-size:{size}px;fill:{color};font-weight:{weight}" {extra}>{esc(value)}</text>')


def rect(x, y, w, h, fill='#ffffff', stroke=LINE, radius=13, extra=''):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.4" {extra}/>')


def window(s, start, end=1.01):
    """Discrete state visibility (not slowly cross-faded contradictory statuses)."""
    events = {0., 1.}
    for at in (start, end):
        if 0 < at < 1:
            events.update((max(0, at - .00001), at))
    return s.track([(t, f'opacity:{int(start <= t < end)}') for t in sorted(events)])


def label_track(s, x, y, states, size=17, color=INK, weight=600, attr=''):
    out = ''
    for i, (at, value) in enumerate(states):
        end = states[i + 1][0] if i + 1 < len(states) else 1.01
        cls = window(s, at, end)
        ink=color
        if isinstance(value,tuple):value,ink=value
        out += f'<g class="{cls}" {attr}>' + text(x, y, value, size, ink, weight) + '</g>'
    return out


def route_particle(s, coords, start, end, color=BLUE, radius=4.5, attr=''):
    if not 0 <= start < end <= 1:
        return ''
    from diagram_layout import Route,path_d
    route=coords if isinstance(coords,Route) else None
    if route:
        attr+=f' data-motion-edge="{route.key}" data-motion-path="{route.d}"'
        coords=route.points
    # Reuse precisely the same path serialization as the visible connector.
    key=tuple(tuple(point) for point in coords)
    if not hasattr(s,'_mechanism_paths'):s._mechanism_paths={}
    if key not in s._mechanism_paths:
        name=s.uid('route')
        d=path_d(key)
        s.rules.append(f'.{s.prefix} .{name}{{offset-path:path("{d}");offset-rotate:0deg;offset-anchor:0px 0px}}')
        s._mechanism_paths[key]=name
    path_cls=s._mechanism_paths[key]
    epsilon=min(.0008,(end-start)/30)
    frames=[(0,'offset-distance:0%;opacity:0')]
    if start>0:frames.append((start,'offset-distance:0%;opacity:0'))
    frames.extend([(start+epsilon,'offset-distance:0%;opacity:1'),(end-epsilon,'offset-distance:100%;opacity:1'),(end,'offset-distance:100%;opacity:0')])
    if end<1:frames.append((1,'offset-distance:100%;opacity:0'))
    cls=s.track(frames)
    return (f'<circle cx="0" cy="0" r="{radius}" class="{path_cls} {cls}" fill="{color}" '
            f'stroke="#fff" stroke-width="1.5" {attr}/>')


def svg(s, body, title, width, height, mobile=False):
    uid = s.uid('mechanism-title')
    kind = 'mechanism-narrow' if mobile else 'mechanism-wide'
    return (f'<svg class="mechanism-svg {kind}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="{uid}"><title id="{uid}">{esc(title)}</title>{body}</svg>')


def style(s):
    p=s.prefix
    s.rules.append(f'.{p} .mechanism-svg{{width:100%;height:auto;display:block;overflow:visible}}\n'
                   f'.{p} .mechanism-narrow{{position:absolute;width:0;height:0;overflow:hidden;visibility:hidden}}\n'
                   f'.{p} .mechanism-legend{{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:10px;color:#607890;font-size:12px}}\n'
                   f'.{p} .mechanism-legend span{{display:inline-flex;align-items:center;gap:7px}}\n'
                   f'.{p} .mechanism-legend i{{width:8px;height:8px;border-radius:50%;display:inline-block}}\n'
                   f'.{p} .mechanism-note{{font-size:12px;color:#607890;line-height:1.7;margin-top:12px}}\n'
                   f'@container (max-width:640px){{.{p} .mechanism-wide{{position:absolute;width:0;height:0;overflow:hidden;visibility:hidden}}.{p} .mechanism-narrow{{position:static;width:100%;height:auto;overflow:visible;visibility:visible}}}}')


def legend(entries):
    return '<div class="mechanism-legend">'+''.join(f'<span><i style="background:{color}"></i>{esc(label)}</span>' for color,label in entries)+'</div>'


def cascade_model():
    failures=[.43,.63,.8]
    schedule=[]
    counters={3:0,2:0,1:0}
    for i in range(55):
        at=.025+i*.017
        eligible=[j for j,t in enumerate(failures) if at<t]
        if not eligible:
            schedule.append(dict(at=at,target=None));continue
        selected=eligible[counters[len(eligible)]%len(eligible)]
        counters[len(eligible)]+=1
        schedule.append(dict(at=at,target=selected))
    states=[]
    for at in [0,*failures,1]:
        live=[i for i,f in enumerate(failures) if at<f]
        states.append(dict(at=at,healthy=len(live),shares=[(1/len(live) if i in live else 0) for i in range(3)]))
    return dict(failures=failures,slow_start=.22,routes=schedule,states=states)


def cascade_diagram(s,model,mobile=False):
    from diagram_scenes import cascade_diagram as draw
    return draw(s,model,mobile)


def cascade(s,p):
    if p:raise ValueError('cascade parameters are intentionally fixed illustrative inputs')
    style(s);model=cascade_model()
    s.numeric.update(model)
    s.numeric['shares_sum']=[[v['at'],sum(v['shares'])] for v in model['states'][:-1]]
    content=cascade_diagram(s,model)+cascade_diagram(s,model,True)
    content+=legend([(BLUE,'요청 이동'),(AMBER,'DB 반환 지연'),(RED,'제외 / 대상 없음')])
    content+='<p class="mechanism-note">게이지와 실패 시각은 합성 가정입니다. 점은 경로와 상대적 집중을 표현하며 실제 req/s나 정확한 스레드 수가 아닙니다.</p>'
    s.table('분배 정책의 상태',['설명 시간 비율','사용 가능 대상','서버 1','서버 2','서버 3'],[[v['at'],v['healthy'],*['1/'+str(v['healthy']) if q else '0' for q in v['shares']]] for v in model['states']])
    phases=[(0,'같은 유입, 세 갈래','새 요청은 세 서버로 번갈아 향한다. 각 서버의 몫은 1/3이다.'),(.22,'공유 DB의 반환이 늦어진다','서버 점유가 증가한다. 이 장면에서는 DB 지연을 원인으로 지정했다.'),(.43,'첫 서버 제외 → 두 갈래','헬스체크에 실패한 대상을 빼면 같은 유입을 두 서버가 1/2씩 받는다.'),(.63,'한 서버에 모두 집중','새 요청을 받을 대상이 한 대뿐이므로 모든 새 요청이 그 경로로 향한다.'),(.8,'더 이상 보낼 대상이 없다','세 대상이 모두 제외됐다. 서버만 바꾸기보다 공통 의존성의 회복을 확인한다.')]
    return content,phases


def event_model(p):
    h=p['horizon'];a=p['block_start'];b=p['block_end']
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (h,a,b)) or not 0<a<b<h or not 1<=h<=60:
        raise ValueError('Require finite 0 < block_start < block_end < horizon (1..60)')
    service=min(.015*h,a*.045,(h-b)/20)
    # Tasks: ordinary handlers, two I/O submissions, and one precisely scheduled CPU block.
    pending=[];tasks=[];io=[];serial=0
    def enqueue(ready,kind,label,request_id,duration=service,io_finish=None):
        nonlocal serial
        serial+=1;heapq.heappush(pending,(ready,serial,dict(ready=ready,kind=kind,label=label,request_id=request_id,duration=duration,io_finish=io_finish)))
    enqueue(.12*a,'normal','요청 1',1)
    enqueue(.28*a,'submit','I/O A',2,io_finish=.7*a)
    enqueue(.46*a,'normal','요청 3',3)
    enqueue(.76*a,'submit','I/O B',4,io_finish=a+.48*(b-a))
    enqueue(a,'cpu','CPU 작업',0,b-a)
    for i in range(6):enqueue(a+(b-a)*(i+1)/7,'normal',f'요청 {i+5}',i+5)
    enqueue(b+.6*(h-b),'normal','요청 11',11)
    free=0
    while pending:
        ready,index,item=heapq.heappop(pending);item=dict(item)
        start=max(ready,free);end=start+item['duration'];item.update(start=start,end=end,index=index)
        if item['kind']=='cpu' and abs(start-a)>1e-8:raise ValueError('Unexpected task overlapping CPU start')
        tasks.append(item);free=end
        if item['kind']=='submit':
            finish=max(end+service,item['io_finish']);callback_ready=finish+min(.024*h,(h-b)/30)
            io.append(dict(label=item['label'],request_id=item['request_id'],start=end,finish=finish,ready=callback_ready))
            enqueue(callback_ready,'callback',item['label']+' 완료',item['request_id'])
    events=sorted(set([0,h,a,b]+[v[k] for v in tasks for k in ('ready','start','end') if v[k]<=h]))
    def state(t):
        queued=[v for v in tasks if v['kind']!='cpu' and v['ready']<=t<v['start']]
        done=[v for v in tasks if v['kind'] in ('normal','callback') and v['end']<=t]
        return dict(t=t,queued=len(queued),done=len(done),blocked=a<=t<b)
    return dict(horizon=h,block_start=a,block_end=b,tasks=tasks,io=io,states=[state(t+1e-10) | {'t':t} for t in events],service=service)


def event_diagram(s,model,mobile=False):
    from diagram_scenes import event_diagram as draw
    return draw(s,model,mobile)


def event_loop(s,p):
    style(s);model=event_model(p);s.numeric.update(model)
    h=model['horizon'];aa=model['block_start']/h;bb=model['block_end']/h
    s.numeric.update(block_ms=(model['block_end']-model['block_start'])*1000,block_window=[aa,bb])
    content=event_diagram(s,model)+event_diagram(s,model,True)
    content+=legend([(BLUE,'요청 / JS 작업'),(PURPLE,'I/O / 완료 콜백'),(AMBER,'대기 작업'),(TEAL,'응답 완료')])
    content+='<p class="mechanism-note">합성 요청 11건의 실행 순서를 계산했습니다. 모든 I/O가 libuv 스레드 풀에서 실행되는 것은 아니며, 전체 Node.js 내부 단계를 재현한 것은 아닙니다.</p>'
    s.table('합성 JS 실행 순서',['작업','종류','준비 s','시작 s','완료 s'],[[t['label'],t['kind'],t['ready'],t['start'],t['end']] for t in model['tasks']])
    s.table('독립 I/O와 콜백 준비',['I/O','위임 s','외부 완료 s','콜백 준비 s'],[[t['label'],t['start'],t['finish'],t['ready']] for t in model['io']])
    s.table('동일 타임라인의 대기 / 완료',['시각 s','대기 건수','응답 완료 건수','CPU 점유'],[[t['t'],t['queued'],t['done'],t['blocked']] for t in model['states']])
    ready=model['io'][-1]['ready']/h
    phases=[(0,'기다림을 위임한다','I/O를 맡긴 뒤 JS 실행 스레드는 다른 작업을 처리한다.'),(aa,'CPU 작업이 스레드를 점유한다','루프 회전과 다음 JS 작업 실행은 멈춘다. 새 요청은 대기한다.'),(ready,'I/O 완료 ≠ 콜백 실행','외부 I/O는 끝났지만, 완료 콜백도 같은 대기열에서 차례를 기다린다.'),(bb,'끝난 뒤에야 대기를 처리한다','JS 실행이 재개되면 준비된 작업을 순서대로 처리하고 응답한다.')]
    return content,phases
