"""Layout-first drawing for three existing cases; preserves their numerical models."""
from __future__ import annotations
import math
from diagram_layout import cascade_layout, event_layout, pipeline_layout
from mechanism_scenes import (text, rect, window, label_track, route_particle, svg,
                              BLUE, TEAL, PURPLE, AMBER, RED, INK, MUTED, LINE)
from reference_scene import esc, fmt, piece


def rail(route, color=LINE, cls='', arrow=True):
    out=f'<path data-edge-id="{route.key}" data-edge-kind="{route.kind}" class="{cls}" d="{route.d}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="miter"/>'
    if arrow:
        a,b=route.points[-2:];length=math.dist(a,b);ux=(b[0]-a[0])/length;uy=(b[1]-a[1])/length
        x,y=b[0]-ux*4,b[1]-uy*4
        out+=f'<path class="{cls}" d="M{x-ux*7-uy*3:g},{y-uy*7+ux*3:g} L{x:g},{y:g} L{x-ux*7+uy*3:g},{y-uy*7-ux*3:g}" fill="none" stroke="{color}" stroke-width="1.6"/>'
    return out


def ports(layout):
    points=set()
    for r in layout.routes.values():
        if r.source:points.add(r.points[0])
        if r.target:points.add(r.points[-1])
    return ''.join(f'<circle data-port="{x:g},{y:g}" cx="{x:g}" cy="{y:g}" r="3" fill="#fff" stroke="#839bb5" stroke-width="1.2"/>' for x,y in sorted(points))


def node_rect(n, fill='#fff', stroke=LINE, radius=10):
    return rect(*n.box,fill,stroke,radius,extra=f'data-layout-node="{n.key}"')


def cascade_diagram(s, model, mobile=False):
    l=cascade_layout(mobile);l.record(s);fail=model['failures'];out='';dots=''
    out+=rail(l.routes['arrival'])
    reject=window(s,.8)
    out+=rail(l.routes['rejected'],RED,reject)
    if mobile:
        out+=rail(l.routes['dispatch-trunk'],arrow=False)+rail(l.routes['dependency-trunk'])
        # Explicit shared-trunk junctions. Do not overpaint the common rails per server.
        for i in range(3):
            yy=l.nodes[f's{i}'].port('left')[1]
            out+=f'<circle cx="44" cy="{yy}" r="3" fill="{LINE}"/><circle cx="356" cy="{yy}" r="3" fill="{LINE}"/>'
    for i,at in enumerate(fail):
        live=window(s,0,at);dead=window(s,at)
        edge=l.routes[f'dispatch-branch-{i}' if mobile else f'dispatch-{i}']
        rear=l.routes[f'dependency-branch-{i}' if mobile else f'dependency-{i}']
        # Rail persists after exclusion; red annotation and absence of tokens convey state.
        fade=s.track([(0,'opacity:1'),(at-.00001,'opacity:1'),(at,'opacity:.28'),(1,'opacity:.28')])
        out+=rail(edge,'#8ba6c8',fade)+rail(rear,'#a1b8c7',fade,arrow=not mobile)
        mx,my=edge.at(.52)
        out+=label_track(s,mx,my-15,[(v['at'],('—' if v['shares'][i]==0 else f"1/{v['healthy']}")) for v in model['states'][:-1]],16 if mobile else 17,BLUE,700,f'data-route-share="{i}"')
        if mobile:
            xx,yy=l.nodes[f's{i}'].port('left');cross=(xx-10,yy)
        else:cross=edge.at(.73)
        x,y=cross
        out+=f'<g class="{dead}" data-route-failed="{i}"><circle cx="{x}" cy="{y}" r="9" fill="#fff"/><path d="M{x-4},{y-4} L{x+4},{y+4} M{x+4},{y-4} L{x-4},{y+4}" stroke="{RED}" stroke-width="2"/></g>'
        for item in model['routes']:
            if item['target']!=i:continue
            a=item['at'];b=min(a+.071,at)
            if b-a>.003:dots+=route_particle(s,l.routes[f'dispatch-{i}'],a,b,BLUE,4.7,f'data-route-packet="{i}"')
            a2=a+.075;b2=min(a2+(.055 if a<.22 else .125),at)
            if b2-a2>.004:dots+=route_particle(s,l.routes[f'dependency-{i}'],a2,b2,TEAL if a<.22 else AMBER,4.3)
    n=l.nodes['lb'];x,y,w,h=n.box
    out+=node_rect(n,'#eff5fe','#9ebce7')+text(x+w/2,y+32,'로드밸런서',20,BLUE,700)
    out+=label_track(s,x+w/2,y+60,[(v['at'],f"분배 대상 {v['healthy']} / 3") for v in model['states'][:-1]],16,BLUE,600,'data-routing-count="true"')
    out+=text(x+w/2,y+82,'유입량은 일정',13,MUTED)
    n=l.nodes['db'];x,y,w,h=n.box
    out+=node_rect(n,'#f4fbf8','#9bc8b9')+f'<g class="{window(s,.22)}">'+rect(*n.box,'#fff1f3','#d58b99',10)+'</g>'
    out+=text(x+w/2,y+34,'공유 DB',21,INK,700)
    out+=label_track(s,x+w/2,y+62,[(0,('빠른 반환',TEAL)),(.22,('반환 지연',RED))],17,RED,600)
    out+=text(x+w/2,y+85,'공통 의존성',12,MUTED)
    levels=[[(0,.3),(.22,.32),(fail[0],1)],[(0,.28),(.22,.3),(fail[0],.56),(fail[1],1)],[(0,.26),(.22,.31),(fail[0],.5),(fail[1],.72),(fail[2],1)]]
    for i,at in enumerate(fail):
        n=l.nodes[f's{i}'];x,y,w,h=n.box
        out+=node_rect(n)+f'<g class="{window(s,at)}">'+rect(*n.box,'#fff5f6','#d89ba8',10)+'</g>'
        out+=text(x+16,y+29,f'서버 {i+1}',19,INK,700,'start')
        out+=label_track(s,x+w-52,y+29,[(0,('정상',TEAL)),(.22,('DB 대기',AMBER)),(at,('제외',RED))],15,RED,600)
        bx=x+16;by=y+56;bw=w-32
        out+=rect(bx,by,bw,10,'#eaf0f7','#eaf0f7',4)
        times=sorted({0,.22,at-.00001,at,1,*[t for t,v in levels[i]]})
        bar=s.track([(t,f'transform:scaleX({piece(t,levels[i]):.5f});transform-origin:{bx}px {by}px;fill:{RED if t>=at else BLUE}') for t in times])
        out+=f'<rect data-server-load="{i}" class="{bar}" x="{bx}" y="{by}" width="{bw}" height="10" rx="4"/>'
        out+=label_track(s,x+w/2,y+92,[(0,'스레드 점유 · 설명용'),(at,'헬스체크 실패')],13,MUTED)
    out+=ports(l)
    for item in model['routes']:
        a=item['at'];dots+=route_particle(s,l.routes['arrival'],max(0,a-.016),a,BLUE,4)
        if item['target'] is None:dots+=route_particle(s,l.routes['rejected'],a,min(.999,a+.028),RED,4.5,'data-unroutable="true"')
    out+=dots
    out+=text(l.width/2,l.height-16,'제외된 대상에는 새 요청을 보내지 않는다',15,MUTED,500)
    return svg(s,out,'정렬된 서버, 직선 분배 경로와 공통 DB. 좁은 화면은 두 개의 공유 레인.',l.width,l.height,mobile)


def compressed(seq):
    result=[]
    for t,value in seq:
        if not result or result[-1][1]!=value:result.append((min(1,t),value))
    return result


def event_diagram(s,model,mobile=False):
    l=event_layout(mobile);l.record(s);h=model['horizon'];aa=model['block_start']/h;bb=model['block_end']/h
    loop=l.nodes['loop'];cx=loop.x+loop.w/2;cy=loop.y+loop.h/2;r=loop.w/2
    out='';dots=''
    # This is a containment boundary, not a processing node or a route obstacle.
    out+=rect(cx-r-34,cy-r-48,2*r+68,2*r+86,'#fbfdff','#c8d5e5',14,extra='stroke-dasharray="5 5"')
    out+=text(cx,cy-r-22,'JS 실행 스레드 · 1개',18,MUTED,600)
    for key in ('arrival','dispatch','response','delegate','callback'):
        out+=rail(l.routes[key],PURPLE if key in ('delegate','callback') else LINE)
    if mobile:
        out+=text(314,744,'I/O 위임',17,PURPLE,600)
        out+=text(56,746,'완료 통지',17,PURPLE,600,'start')
    else:
        out+=text(578,426,'① I/O 위임',15,PURPLE,600)
        out+=text(266,498,'② 완료 → 콜백 대기',15,PURPLE,600)
    n=l.nodes['queue'];x,y,w,ht=n.box
    out+=node_rect(n,'#f9fbfe','#bfd0e3')+text(x+w/2,y+28,'대기 작업',20,INK,700)
    out+=label_track(s,x+w/2,y+57,compressed([(v['t']/h,f"{v['queued']}건 대기") for v in model['states']]),18,AMBER,700,'data-queue-label="true"')
    for i in range(8):
        gx=x+(w-148)/2+(i%4)*39;gy=y+78+(i//4)*37
        out+=rect(gx,gy,25,25,'#edf2f8','#dce5f0',5)
        events={0.,1.}
        for st in model['states']:
            t=st['t']/h
            if 0<t<1:events.update([max(0,t-.00001),t])
        def q_at(t):return next(v['queued'] for v in reversed(model['states']) if v['t']<=t*h+1e-8)
        cls=s.track([(t,f'opacity:{int(q_at(t)>i)}') for t in sorted(events)])
        out+=f'<rect class="{cls}" data-queue-slot="{i}" x="{gx}" y="{gy}" width="25" height="25" rx="5" fill="#e2ad47"/>'
    out+=text(x+w/2,y+ht-16,'요청 + 완료 콜백',14,MUTED)
    n=l.nodes['answer'];x,y,w,ht=n.box
    out+=node_rect(n,'#f3faf7','#aacdbd')+text(x+w/2,y+28,'응답 완료',20,TEAL,700)
    out+=label_track(s,x+w/2,y+64,compressed([(v['t']/h,f"{v['done']}건") for v in model['states']]),27,TEAL,700,'data-completed-label="true"')
    out+=text(x+w/2,y+ht-16,'합성 요청 11건',14,MUTED)
    out+=f'<circle data-layout-node="loop" cx="{cx}" cy="{cy}" r="{r}" fill="#eef5ff" stroke="#a4bfdf" stroke-width="2.4"/>'
    out+=f'<circle cx="{cx}" cy="{cy}" r="{r-12}" fill="none" stroke="#d8e6f8" stroke-width="1" stroke-dasharray="3 7"/>'
    out+=f'<circle class="{window(s,aa,bb)}" cx="{cx}" cy="{cy}" r="{r}" fill="#fff4ee" stroke="{RED}" stroke-width="2.4"/>'
    angle=lambda t:1440*min(t,aa)+max(0,t-bb)*2100
    rotate=s.track([(t,f'transform:rotate({angle(t):.4f}deg);transform-origin:{cx}px {cy}px') for t in sorted({0,aa,bb,1})])
    out+=f'<g class="{rotate}" data-event-rotor="true">'
    for j in range(5):
        ang=-j*math.pi/18
        out+=f'<circle cx="{cx+r*math.cos(ang)}" cy="{cy+r*math.sin(ang)}" r="{7-j*.75}" fill="{BLUE}" opacity="{1-j*.16}"/>'
    out+='</g>'
    out+=label_track(s,cx,cy-14,[(0,'이벤트 루프'),(aa,'CPU 작업 실행'),(bb,'다시 처리 중')],22,INK,700)
    out+=label_track(s,cx,cy+16,[(0,'위임하고 계속 순환'),(aa,f"{fmt(model['block_end']-model['block_start'])}초 콜백 실행 정지"),(bb,'밀린 작업을 순서대로')],14,RED,600)
    out+=label_track(s,cx,cy+41,[(0,'실행 가능'),(aa,'대기열 증가'),(bb,'응답 재개')],14,MUTED)
    n=l.nodes['io'];x,y,w,ht=n.box
    out+=node_rect(n,'#f7f3fd','#c8b4e4')+text(x+w/2,y+29,'OS / 외부 I/O',20,PURPLE,700)
    out+=text(x+w/2,y+52,'JS와 독립적으로 진행',14,MUTED)
    for i,item in enumerate(model['io']):
        xx=x+w*(.27+.46*i);yy=y+84
        out+=label_track(s,xx,yy,[(0,item['label']+' 대기'),(item['start']/h,item['label']+' 실행'),(item['finish']/h,item['label']+' 완료')],14,PURPLE,600)
        start=item['start']/h;finish=item['finish']/h
        dots+=route_particle(s,l.routes['delegate'],start,min(finish,start+.06),PURPLE,5.4,'data-io-delegation="true"')
        if item['ready']<=h:dots+=route_particle(s,l.routes['callback'],finish,item['ready']/h,PURPLE,5.4,'data-callback-return="true"')
    for task in model['tasks']:
        if task['kind']=='cpu':continue
        start=task['start']/h;end=task['end']/h;color=PURPLE if task['kind'] in ('callback','submit') else BLUE
        if task['kind']!='callback':
            at=task['ready']/h;dots+=route_particle(s,l.routes['arrival'],max(0,at-.025),at,color,5)
        if start<1:
            in_end=min(end,start+(end-start)*.33)
            dots+=route_particle(s,l.routes['dispatch'],start,in_end,color,5.5,'data-js-dispatch="true"')
            # The circular execution path is semantic. Its endpoints meet the correct outgoing port.
            a0=math.pi/2 if mobile else math.pi
            a1=0 if mobile and task['kind']=='submit' else -math.pi/2 if mobile or task['kind']=='submit' else 0
            arc=[(cx+r*math.cos(a0+(a1-a0)*j/48),cy-r*math.sin(a0+(a1-a0)*j/48)) for j in range(49)]
            # Make endpoints exact, without tiny trigonometric rounding gaps.
            arc[0]=l.routes['dispatch'].points[-1]
            arc[-1]=l.routes['delegate' if task['kind']=='submit' else 'response'].points[0]
            dots+=route_particle(s,arc,in_end,min(1,end),color,5.5,'data-js-execution="true" data-motion-kind="internal-orbit"')
            if task['kind'] in ('normal','callback') and end<1:dots+=route_particle(s,l.routes['response'],end,min(1,end+.033),TEAL,5.5,'data-response-packet="true"')
    out+=ports(l)+dots
    delayed=next(v for v in model['io'] if v['ready']>=model['block_start'])
    note=window(s,delayed['ready']/h,bb)
    out+=f'<g class="{note}" data-callback-wait-note="true">'
    if mobile:out+=text(l.width/2,942,'I/O B 완료 · 콜백은 대기',18,PURPLE,600)
    else:out+=text(l.width/2,611,'I/O B는 완료됐지만, 콜백은 JS 스레드를 기다린다',17,PURPLE,600)
    out+='</g>'+text(l.width/2,l.height-15,'외부 I/O 완료와 JS 실행 재개는 서로 다르다',14,MUTED)
    result=svg(s,out,'정렬된 작업 흐름. 직선 입출력과 분리된 I/O 위임 및 콜백 반환 레인.',l.width,l.height,mobile)
    return result if mobile else result.replace('viewBox="0 0 1000 646"','viewBox="0 112 1000 534"')


def pipeline_diagram(s,rows,p,mobile=False):
    l=pipeline_layout(mobile);l.record(s);h=p['horizon'];change=p['change_time']/h;maxq=max(r['q'] for r in rows)
    out='';dots=''
    for route in l.routes.values():out+=rail(route)
    labels={'gateway':'Gateway','application':'Application','database':'DB'}
    for key,title in labels.items():
        n=l.nodes[key];x,y,w,ht=n.box;cap=p[key+'_capacity'];col=RED if key=='application' else TEAL
        out+=node_rect(n)+text(x+w/2,y+28,title,21,INK,700)+text(x+w/2,y+53,f'{fmt(cap)} req/s',16,MUTED)
        if key=='application':
            out+=f'<g class="{window(s,change)}">'+rect(*n.box,'none','#d89ba8',10)+'</g>'
        bx=x+18;by=y+76;bw=w-36
        out+=rect(bx,by,bw,9,'#eaf0f7','#eaf0f7',4)
        seq=[]
        for row in rows:
            value=row['rate'] if key=='gateway' else row['served_rate']
            seq.append((row['t']/h,f'transform:scaleX({min(1,value/cap):.6f});transform-origin:{bx}px {by}px'))
        cls=s.track(seq)
        out+=f'<rect class="{cls}" x="{bx}" y="{by}" width="{bw}" height="9" rx="4" fill="{col}"/>'
        out+=label_track(s,x+w/2,y+110,[(0,'처리 한도 안쪽'),(change,'처리 한도 도달' if key=='application' else '처리 여유 유지')],14,col)
    n=l.nodes['queue'];x,y,w,ht=n.box
    out+=node_rect(n,'#fffaf2','#dfcca8')+text(x+w/2,y+28,'대기 공간',21,INK,700)
    out+=label_track(s,x+w/2,y+52,[(0,'유입을 바로 전달'),(change,'초과분이 쌓이는 곳')],14,AMBER)
    for i in range(12):
        gx=x+(w-134)/2+(i%6)*23;gy=y+68+(i//6)*22
        out+=rect(gx,gy,18,16,'#eee8dd','#e8e0d1',3)
        at=next((r['t']/h for r in rows if r['q']>=maxq*(i+1)/12),1)
        cls=s.reveal(max(change,at-.025))
        out+=f'<rect class="{cls}" x="{gx}" y="{gy}" width="18" height="16" rx="3" fill="#d6a044"/>'
    # Symbolic stream densities follow the cumulative model; the diagram does not count packets.
    incoming=rows[-1]['incoming'];served=rows[-1]['served']
    def arrivals(field,total,count):
        return [next(row['t']/h for row in rows if row[field]>=total*(i+.3)/count) for i in range(count)]
    for i,at in enumerate(arrivals('incoming',incoming,24)):
        for key,offset in [('arrival',0),('gateway-queue',.023)]:
            start=min(.997,at+offset);end=min(.999,start+.055)
            if end-start>.002:dots+=route_particle(s,l.routes[key],start,end,BLUE,4.7)
    for i,at in enumerate(arrivals('served',served,18)):
        for key,offset in [('queue-application',0),('application-database',.022),('exit',.044)]:
            start=min(.997,at+offset);end=min(.999,start+.055)
            if end-start>.002:dots+=route_particle(s,l.routes[key],start,end,TEAL,4.7)
    out+=ports(l)+dots
    out+=text(l.width/2,l.height-17,'점·블록은 흐름과 누적의 상징입니다',14,MUTED)
    return svg(s,out,'Gateway, 대기 공간, Application, DB를 같은 축에 정렬한 파이프라인',l.width,l.height,mobile)


def pipeline_flow(s,rows,p):
    from mechanism_scenes import style,legend
    style(s)
    return pipeline_diagram(s,rows,p)+pipeline_diagram(s,rows,p,True)+legend([(BLUE,'유입 흐름'),(TEAL,'처리 흐름'),(AMBER,'앞쪽 대기 누적')])
