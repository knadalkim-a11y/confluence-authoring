"""Case-specific explanations built from reusable time/flow/distribution primitives.

This module is not a monitoring tool. Models are intentionally small and deterministic.
See the case manifest for the provenance, abstraction and limits of each example.
"""
from __future__ import annotations
import math, heapq
from reference_scene import ReferenceScene, samples, piece, esc, fmt, clamp, COLORS
B,R,P,G,A=COLORS

def finite(v,name,lo=0,hi=1e6):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
        raise ValueError(f'{name}: finite number in [{lo},{hi}] required')
    return v

def percentile(values,counts,q):
    if len(values)!=len(counts) or not 1<=len(values)<=30 or values!=sorted(set(values)):
        raise ValueError('Expected equal-length sorted unique values/frequencies')
    for v in values:finite(v,'value')
    for n in counts:
        finite(n,'count',0,1000)
        if n!=int(n):raise ValueError('Counts must be integer')
    total=sum(counts)
    if not total:raise ValueError('Empty distribution')
    rank=math.ceil(q*total);running=0
    for value,n in zip(values,counts):
        running+=n
        if running>=rank:return value
    raise AssertionError('unreachable')

def stats(values,counts):
    p={f'p{int(q*100)}':percentile(values,counts,q) for q in [.5,.95,.99]}
    p.update(n=sum(counts),mean=sum(v*n for v,n in zip(values,counts))/sum(counts));return p

def fluid_queue(p,limit=None,steps=200):
    before=finite(p['before_rate'],'before_rate');after=finite(p['after_rate'],'after_rate')
    capacity=finite(p.get('capacity',p.get('application_capacity')),'capacity',.001)
    horizon=finite(p['horizon'],'horizon',.1,120);change=finite(p['change_time'],'change_time',0,horizon)
    if limit is not None:finite(limit,'queue_limit')
    # Include the change instant exactly, so integration is valid even after customization.
    times=sorted(set([i*horizon/steps for i in range(steps+1)]+[change]))
    q=inc=out=rej=0.0;rows=[dict(t=0,rate=before,served_rate=before if before<capacity else capacity,q=0,incoming=0,served=0,rejected=0)]
    for t0,t1 in zip(times,times[1:]):
        rate=before if t0<change-1e-10 else after;dt=t1-t0;incoming=rate*dt
        served=min(q+incoming,capacity*dt);q+=incoming-served
        rejected=max(0,q-limit) if limit is not None else 0;q-=rejected
        inc+=incoming;out+=served;rej+=rejected
        rows.append(dict(t=t1,rate=rate,served_rate=served/dt,q=round(q,9),incoming=round(inc,9),served=round(out,9),rejected=round(rej,9)))
    return rows

def pool_model(p):
    w=p['workers']
    if isinstance(w,bool) or not isinstance(w,int) or not 1<=w<=12:raise ValueError('workers integer 1..12')
    for k in ['arrival_interval','normal_service','slow_service','horizon','arrival_end']:finite(p[k],k,.02,120)
    for k in ['slow_start','recovery']:finite(p[k],k,0,p['horizon'])
    if p['normal_service']>=p['slow_service']:raise ValueError('slow_service must exceed normal_service')
    if not 0<p['slow_start']<p['recovery']<p['horizon'] or p['arrival_end']>p['horizon']:raise ValueError('Invalid event ordering')
    count=math.floor(p['arrival_end']/p['arrival_interval']+1e-9)
    if count>180:raise ValueError('At most 180 symbolic requests')
    free=[(0,i) for i in range(w)];heapq.heapify(free);jobs=[]
    for i in range(1,count+1):
        arrive=i*p['arrival_interval'];available,slot=heapq.heappop(free);start=max(arrive,available)
        service=p['slow_service'] if p['slow_start']<=start<p['recovery'] else p['normal_service'];end=start+service
        heapq.heappush(free,(end,slot));jobs.append(dict(id=i,arrive=arrive,start=start,end=end,slot=slot,service=service,wait=start-arrive))
    return jobs

def pool_state(jobs,t):
    return dict(arrived=sum(j['arrive']<=t for j in jobs),active=sum(j['start']<=t<j['end'] for j in jobs),queued=sum(j['arrive']<=t<j['start'] for j in jobs),completed=sum(j['end']<=t for j in jobs))

def phase(*items):return [(at,title,description) for at,title,description in items]

def traffic(s,p):
    base=lambda t:1800+6300*(max(0,math.sin(2*math.pi*(t*2-.22)))**2)+250*math.sin(t*math.pi*16)
    fs=[('평소 반복',lambda t:base(t),G,()),('급락',lambda t:base(t) if t<.7 else 180+80*math.sin(t*32),R,[(.7,'급락',R)]),('급증',lambda t:base(t)*.45 if t<.55 else 8500+160*math.sin(t*24),A,[(.55,'급증',A)]),('주기적 스파이크',lambda t:min(10000,base(t)+7000*sum(math.exp(-((t-u)/.009)**2) for u in [4/48,28/48])),P,[(4/48,'04시',P),(28/48,'다음 04시',P)])]
    cards=[s.chart(title,[(title,samples(fn,161),color)],'req/s',10000,events=ev,x_label='48시간 합성 관찰',x_ticks=[(0,'0h'),(.5,'24h'),(1,'48h')]) for title,fn,color,ev in fs]
    return s.grid(*cards),phase((0,'평소 모양','같은 시간대의 반복 형태를 먼저 본다.'),(.5,'방향과 반복','급락과 급증은 서로 다른 조사 경로를 제안한다.'),(.86,'단서이지 판정은 아니다','주기·유입 경로·로그를 함께 확인한다.'))

def distributions(s,p):
    pairs=[('서버 A',p['a_values'],p['a_counts']),('서버 B',p['b_values'],p['b_counts'])];cards=[]
    upper=max(p['a_values']+p['b_values'])*1.14;upper=max(upper,1000)
    for title,values,counts in pairs:
        st=stats(values,counts)
        if st['n']>120:raise ValueError('At most 120 displayed observations per distribution')
        s.numeric[title]=st
        X=lambda v:54+v/upper*418
        body='<line x1="54" x2="474" y1="245" y2="245" stroke="#becddd"/>'
        order=[]
        for stack in range(max(counts)):
            for v,n in zip(values,counts):
                if stack<n:order.append((v,stack))
        gap=min(7,125/max(counts));radius=min(4,gap*.43)
        for i,(v,stack) in enumerate(order):
            x=X(v);y=241-stack*gap;at=.015+i*.39/max(1,len(order))
            cls=s.track([(0,f'transform:translateY({80-y}px);opacity:0'),(at,f'transform:translateY({80-y}px);opacity:0'),(at+.07,'transform:translateY(0px);opacity:1'),(1,'transform:translateY(0px);opacity:1')])
            body+=f'<circle class="{cls}" cx="{x}" cy="{y}" r="{radius}" fill="{P if v>=400 else B}"/>'
        for i,(key,label,color) in enumerate([('mean','평균',B),('p50','P50',G),('p95','P95',A),('p99','P99',R)]):
            val=st[key];at=.48+i*.1;cls=s.reveal(at);x=X(val);y=20+i*24
            anchor='end' if val/upper>.66 else 'start';dx=-4 if anchor=='end' else 4
            body+=f'<g class="{cls}"><line x1="{x}" x2="{x}" y1="{y+5}" y2="245" stroke="{color}" stroke-dasharray="4 4"/><text x="{x+dx}" y="{y}" text-anchor="{anchor}" style="fill:{color}">{label} {esc(fmt(val))}</text></g>'
        for val in [0,upper/2,upper]:body+=f'<text x="{X(val)}" y="270" text-anchor="middle">{fmt(val)}</text>'
        s.table(title+' · 원시 이산값/빈도',['ms','건수'],list(zip(values,counts)))
        cards.append(s.panel(title,s.svg(body,title+'의 점 분포와 백분위',285),'가로: ms · 점 1개 = 요청 1건',f'표본 {st["n"]}건 · 평균 {fmt(st["mean"])}ms · P95 {fmt(st["p95"])}ms · P99 {fmt(st["p99"])}ms'))
    return s.grid(*cards),phase((0,'표본을 쌓는다','점 하나가 요청 한 건이다. 두 분포의 모양을 비교한다.'),(.47,'평균을 더한다','각 표본의 가중 평균을 계산해 같은 축에 표시한다.'),(.75,'꼬리를 읽는다','P50·P95·P99는 동일한 표본에서 계산한다.'))

def split_diagram(s,mode='failure'):
    top='성공 집계' if mode=='failure' else '캐시 HIT';bottom='즉시 거부' if mode=='failure' else 'DB MISS'
    body='<path class="mr-rail" d="M45 90 H175 L320 48 H450 M175 90 L320 148 H450"/>'
    body+=s.box(5,63,90,54,'요청')+s.box(335,22,160,50,top)+s.box(335,123,160,50,bottom,color=R)
    body+=s.token_stream(96,90,335,48,0,.42,8,B)
    if mode=='failure':
        body+=s.token_stream(96,90,335,148,.42,1,9,R)+s.token_stream(96,90,335,48,.42,1,9,B)
    else:
        body+=s.token_stream(96,90,335,148,.42,.73,8,R)+s.token_stream(96,90,335,48,.73,1,7,B)
    return s.panel('요청 경로',s.svg(body,'요청이 정상 또는 실패 경로로 나뉘는 개념도',190),'점의 개수는 실제 처리 건수와 대응하지 않는 상징 표현')

def survivorship(s,p):
    pre=stats([80,140],[900,99]);post=stats([75],[500])
    e0=1/1000*100;e1=500/1000*100
    error=samples(lambda t:piece(t,[(0,e0),(.4,e0),(.42,e1),(1,e1)]))
    latency=samples(lambda t:piece(t,[(0,pre['p99']),(.4,pre['p99']),(.46,post['p99']),(1,post['p99'])]))
    s.numeric['populations']={'before':{'success':999,'failure':1,'p99':pre['p99']},'after':{'success':500,'failure':500,'p99':post['p99']}}
    s.table('집계 분모와 백분위',['구간','전체','성공','실패','성공 요청 P99 ms'],[['이전',1000,999,1,pre['p99']],['이후',1000,500,500,post['p99']]])
    c=s.grid(s.chart('에러율',[('전체 요청',error,R)],'%',100,[(.4,'거부 시작',R)]),s.chart('성공 요청의 P99',[('성공 집계',latency,P)],'ms',200,[(.4,'표본 변경',R)]))
    s.numeric.update(error_final=50,p99_success_final=75,latency_population='successful requests only')
    return s.stack(c,split_diagram(s)),phase((0,'분모를 확인한다','에러율은 전체 요청, 지연은 성공 요청만 집계하는 예시다.'),(.42,'빠르게 실패한다','실패한 요청은 이 지연 분포에서 제외된다.'),(.8,'좋아 보이는 지연의 함정','P99 하락을 전체 사용자 경험의 회복으로 읽지 않는다.'))

def cpu_scenarios():
    """Synthetic CPU/P99 pairs on normalized time [0,1]. Knot times are the scenario events."""
    return [dict(key='A',title='정상',cpu=lambda t:50+12*math.sin(t*9),p99=lambda t:65+9*math.sin(t*9),color=G,events={}),
            dict(key='B',title='낮은 CPU · 높은 지연',cpu=lambda t:25+3*math.sin(t*17),p99=lambda t:piece(t,[(0,75),(.35,75),(.6,900),(1,900)]),color=A,events=dict(p99_rise=.35,p99_plateau=.6)),
            dict(key='C',title='CPU 포화',cpu=lambda t:piece(t,[(0,45),(.2,45),(.4,100),(1,100)]),p99=lambda t:piece(t,[(0,70),(.2,70),(.4,920),(1,940)]),color=R,events=dict(cpu_rise=.2,cpu_saturated=.4))]

def cpu(s,p):
    scenarios=[(x['title'],x['cpu'],x['p99'],x['color']) for x in cpu_scenarios()]
    groups=[]
    for title,cpu,lat,color in scenarios:
        groups.append(s.panel(title,s.grid(s.chart('CPU 사용률',[(title,samples(cpu),B)],'%',100),s.chart('P99 응답 시간',[(title,samples(lat),P)],'ms',1000)),summary='서로 다른 가설을 구분하는 합성 사례'))
    return s.stack(*groups),phase((0,'두 지표를 짝짓는다','CPU와 P99를 같은 시각에서 읽는다.'),(.4,'대기와 연산을 구분한다','CPU가 낮아도 기다리는 요청의 지연은 높아질 수 있다.'),(.84,'추가 근거가 필요하다','트래픽·I/O·풀·프로파일로 원인 가설을 확인한다.'))

def throttling(s,p):
    period=finite(p['period_ms'],'period',1,1000);quota=finite(p['quota_ms'],'quota',1,period);low=finite(p['low_use_ms'],'low_use',.001,quota)
    n=p['periods'];change=p['load_start_period']
    if not isinstance(n,int) or not 3<=n<=10 or not isinstance(change,int) or not 1<=change<n:raise ValueError('Invalid period count/change')
    rows=[];parts=[]
    for i in range(n):
        used=low if i<change else quota;blocked=0 if i<change else period-quota
        w=420;runw=w*used/period;blockw=w*blocked/period;start=i/n;end=(i+1)/n
        run=s.track([(0,'width:0px'),(start+.001,'width:0px'),(start+(end-start)*used/period,f'width:{runw}px'),(1,f'width:{runw}px')])
        body=f'<rect x="55" y="10" width="420" height="28" rx="5" fill="#eaf0f7"/><rect class="{run}" x="55" y="10" width="{runw}" height="28" fill="{B}"/>'
        if blocked:
            at=start+(end-start)*quota/period
            block=s.track([(0,'width:0px'),(at,'width:0px'),(end,f'width:{blockw}px')]+([] if end==1 else [(1,f'width:{blockw}px')]))
            body+=f'<rect class="{block}" x="{55+runw}" y="10" width="{blockw}" height="28" fill="#f3cfb9"/>'
            for j in range(7):body+=f'<line class="{s.reveal(min(.95,at))}" x1="{55+runw+j*blockw/7}" y1="38" x2="{55+runw+j*blockw/7+12}" y2="10" stroke="#b1774c"/>'
        body+=f'<text x="55" y="64">실행 {fmt(used)}ms</text><text x="475" y="64" text-anchor="end">'+(f'강제 대기 {fmt(blocked)}ms' if blocked else '할당량 잔여')+'</text>'
        parts.append(s.panel(f'주기 {i+1}',s.svg(body,f'주기 {i+1} 실행과 대기',77),f'{fmt(period)}ms · CPU 예산 {fmt(quota)}ms'))
        rows.append([i+1,used,blocked,period-used-blocked])
    s.table('CPU 시간 예산',['주기','실행 ms','스로틀 ms','그 외 ms'],rows);s.numeric.update(quota=quota,period=period,rows=rows)
    return s.grid(*parts),phase((0,'낮은 부하','CPU 시간 예산보다 적게 실행하고 끝난다.'),(change/n,'예산 소진','부하가 커지면 예산 소진 뒤 다음 주기를 기다린다.'),(.87,'지표의 뜻을 구분한다','사용한 시간과 실행이 제한된 시간을 따로 본다.'))

def memory(s,p):
    normal=lambda t:35+38*((t*7)%1)
    def leaking(t):
        if t<.82:return min(100,30+int(t*7)*9+38*((t*7)%1))
        if t<.85:return 2
        return 13+25*((t-.85)/.15)
    a=samples(normal,225);b=samples(leaking,225)
    content=s.grid(s.chart('정상 GC 리듬',[('힙',a,B)],'%',110,[(.5,'바닥 유지',G)],threshold=100),s.chart('잔존량 증가',[('힙',b,R)],'%',110,[(.82,'OOM',R),(.85,'재시작',P)],threshold=100))
    floorsA=[(i/7,35) for i in range(1,7)];floorsB=[(i/7,30+i*9) for i in range(1,6)]
    content+=s.grid(s.chart('GC 후 최저점 비교',[('정상',floorsA,G),('상승',floorsB,R)],'%',110,x_label='같은 GC 구간'))
    return content,phase((0,'톱니를 본다','증가와 수거의 반복은 두 경우에 모두 나타난다.'),(.43,'GC 뒤 바닥을 비교한다','정상과 잔존량 증가를 수거 이후의 값으로 구분한다.'),(.85,'낮아진 값과 원인 해결은 다르다','재시작은 관찰 상태를 바꾸지만 누수 원인을 제거했다는 뜻은 아니다.'))

def spike(s,p):
    heap=samples(lambda t:30+30*((t*6)%1) if t<.6 else piece(t,[(.6,65),(.68,65),(.7,88),(1,93)]),201)
    chart=s.chart('힙 사용률',[('힙',heap,B)],'%',110,[(.6,'14:32:05',R)],threshold=100,x_label='합성 로그와 같은 시각',x_ticks=[(0,'14:31:50'),(1,'14:32:15')])
    logs=[(.08,'14:31:52  GET /items 시작'),(.24,'14:31:56  GET /cart 시작'),(.4,'14:32:00  POST /orders 시작'),(.52,'14:32:03  GET /items 시작'),(.6,'14:32:05  GET /export?scope=all 시작'),(.8,'14:32:10  GET /cart 시작')]
    body=''.join('<div class="mr-log '+s.reveal(at)+'"'+(' style="background:#fff0f2;border-left:3px solid #ad3947"' if at==.6 else '')+'>'+esc(label)+'</div>' for at,label in logs)
    return s.stack(chart,s.panel('합성 액세스 로그',body,'표시된 시각은 요청 시작 시각')),phase((0,'평소 구간','반복되는 수거 리듬과 요청을 관찰한다.'),(.6,'같은 시각으로 정렬','계단 변화와 대용량 요청의 시작을 나란히 놓는다.'),(.87,'가설을 검증한다','동시 발생은 단서다. 요청 크기와 메모리 프로파일로 확인한다.'))

def pool(s,p):
    jobs=pool_model(p);h=p['horizon'];w=p['workers']
    times=sorted(set([0,h]+[j[k] for j in jobs for k in ['arrive','start','end'] if j[k]<=h]))
    sampled=[(t,pool_state(jobs,t+1e-9)) for t in times]
    s.numeric.update(jobs=jobs,states=sampled,max_queue=max(v['queued'] for _,v in sampled))
    points=lambda field:[[t/h,v[field]] for t,v in sampled]
    chart=s.grid(s.chart('사용 중 슬롯',[('활성',points('active'),B)],'칸',w,[(p['slow_start']/h,'지연 시작',R),(p['recovery']/h,'회복',G)]),s.chart('대기열',[('큐',points('queued'),A)],'건',max(1,s.numeric['max_queue'])*1.15,[(p['slow_start']/h,'지연',R),(p['recovery']/h,'회복',G)]))
    body='<path class="mr-rail" d="M65 98 H435"/>'+s.box(2,70,82,57,'유입')+s.box(402,70,96,57,'처리', '반납',G)
    columns=4;cellw=49;cellh=32;gap=14;left=120;top=42
    for slot in range(w):
        x=left+(slot%columns)*(cellw+gap);y=top+(slot//columns)*(cellh+gap)
        occupied=[j for j in jobs if j['slot']==slot]
        boundaries={0.0,h}
        for j in occupied:
            for t in [j['start'],j['end']]:
                if 0<=t<=h:
                    boundaries.add(t);boundaries.add(max(0,t-h*.0001))
        frames=[]
        for t in sorted(boundaries):
            busy=any(j['start']<=t<j['end'] for j in occupied)
            frames.append((t/h,'fill:#a9c6ef' if busy else 'fill:#f7faff'))
        cls=s.track(frames)
        body+=f'<rect data-mr-slot="{slot}" class="{cls}" x="{x}" y="{y}" width="{cellw}" height="{cellh}" rx="5" stroke="#9fb6d0"/><text x="{x+cellw/2}" y="{y+22}" text-anchor="middle">{slot+1}</text>'
    body+=s.token_stream(85,97,130,97,0,1,16)+s.token_stream(360,97,400,97,0,1,12)
    final=pool_state(jobs,h)
    diagrams=s.panel(f'{w}개 슬롯의 실제 모델 점유',s.svg(body,'각 슬롯이 작업 시작부터 반환까지 점유되는 상태',195),'양 끝의 이동 점은 경로 표시이며 작업 건수가 아니다')
    s.table('FIFO 요청 사건표',['요청','도착 s','시작 s','완료 s','슬롯','대기 s'],[[j['id'],j['arrive'],j['start'],j['end'],j['slot']+1,j['wait']] for j in jobs])
    metrics=s.metrics([('요청 수',str(len(jobs)),'모델에 투입한 건수'),('최대 대기',str(s.numeric['max_queue'])+'건','각 사건 시점에서 계산'),('종료 대기',str(final['queued'])+'건',f'관찰 {h:g}초 기준')])
    return s.stack(diagrams,metrics,chart),phase((0,'정상 처리','같은 간격으로 요청이 들어오고 빈 슬롯을 얻는다.'),(p['slow_start']/h,'처리 지연','반납이 늦어지며 슬롯과 대기열이 점유된다.'),(p['recovery']/h,'처리 속도 회복','회복 전에 시작한 긴 작업까지 즉시 끝나지는 않는다.'),(.9,'수지를 확인한다','도착 = 완료 + 실행 중 + 대기. 각 값을 사건표로 검증한다.'))

def cascade(s,p):
    from mechanism_scenes import cascade as mechanism_cascade
    return mechanism_cascade(s,p)


def event_loop(s,p):
    from mechanism_scenes import event_loop as mechanism_event_loop
    return mechanism_event_loop(s,p)

def pipeline_flow(s,rows,p):
    from diagram_scenes import pipeline_flow as draw
    return draw(s,rows,p)


def pipeline(s,p):
    for key in ['gateway_capacity','database_capacity']:finite(p[key],key,.001)
    if not p['before_rate']<=p['application_capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    if p['gateway_capacity']<max(p['before_rate'],p['after_rate']) or p['database_capacity']<p['application_capacity']:
        raise ValueError('This example assumes only Application is the bottleneck')
    rows=fluid_queue(p);h=p['horizon'];end=rows[-1]
    s.numeric.update(rows=rows,final=end)
    curves=[('유입',[[r['t']/h,r['rate']] for r in rows],B),('처리',[[r['t']/h,r['served_rate']] for r in rows],G)]
    c=s.grid(s.chart('유입과 실제 처리',curves,'req/s',max(p['after_rate'],p['before_rate'])*1.2,[(p['change_time']/h,'유입 변화',R)],x_end=f'{h:g}s'),s.chart('Application 앞의 대기',[('잔여',[[r['t']/h,r['q']] for r in rows],A)],'건',max(1,end['q'])*1.2,x_end=f'{h:g}s'))
    s.table('유입·처리·잔여 수지',['관찰 s','누적 유입','누적 처리','잔여'],[[r['t'],r['incoming'],r['served'],r['q']] for r in rows[::10]])
    m=s.metrics([('증가 후 유입',f'{fmt(p["after_rate"])} /s','모델 입력'),('처리 한도',f'{fmt(p["application_capacity"])} /s','Application'),('관찰 종료 대기',fmt(end['q'])+'건',f'모델 {h:g}초 지점')])
    return s.stack(pipeline_flow(s,rows,p),m,c),phase((0,'처리 한도 안쪽','정상 유입에서는 앞쪽에 대기가 거의 없다.'),(p['change_time']/h,'유입 증가','Application 한도를 초과한 유입은 대기가 된다.'),(.85,'대기의 위치','앞쪽 적체와 뒤쪽 여유를 함께 확인한다.'))

def utilization(s,p):
    points=[[i/100, (i/100)/(1-i/100)] for i in range(96)]
    # Explicit x=rho normalized to plot [0,1], so 80% marker stays at x=.8.
    chart=s.chart('M/M/1 모델의 평균 대기', [('Wq / Wq(50%)',points,B)],'배',20,[(.8,'80% 예시',A)],x_label='사용률 ρ',x_ticks=[(0,'0%'),(.5,'50%'),(.8,'80%'),(1,'100%')])
    vals=[(rho,rho/(1-rho)) for rho in [.5,.7,.8,.9,.95]]
    s.numeric['normalized_wait']=vals;s.table('모델 기준점',['사용률','대기 배율'],[[f'{r*100:g}%',v] for r,v in vals])
    return chart+s.metrics([(f'사용률 {r*100:g}%',fmt(v)+'배','50% 대기를 1로 정규화') for r,v in vals]),phase((0,'비례 증가가 아니다','사용률이 올라갈수록 여유 슬롯을 바로 얻기 어려워진다.'),(.78,'가파른 구간','정해진 모델의 곡선이지 보편적인 80% 위험선은 아니다.'),(.9,'가정을 함께 읽는다','정상 상태·단일 서버·분포 가정과 서비스 시간을 확인한다.'))

def bounded(s,p):
    limit=finite(p['queue_limit'],'queue_limit',.001,1000)
    if not p['before_rate']<=p['capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    unbounded=fluid_queue(p);bounded=fluid_queue(p,limit)
    h=p['horizon'];a=unbounded[-1];b=bounded[-1]
    s.numeric.update(unbounded=unbounded,bounded=bounded)
    parts=[]
    for title,rows,col in [('대기 상한 없음',unbounded,R),('대기 상한 적용',bounded,G)]:
        q=rows[-1]['q'];out=rows[-1]['served'];rej=rows[-1]['rejected']
        body=s.chart('잔여 대기',[('대기',[[r['t']/h,r['q']] for r in rows],col)],'건',max(1,a['q'])*1.15,[(p['change_time']/h,'과부하',A)],x_end=f'{h:g}s')
        # Buffer glyph complements the common-scale chart. Labels state the separate scales.
        cells=16 if title=='대기 상한 없음' else 8;scale=max(1,q) if title=='대기 상한 없음' else limit
        glyph=''
        for j in range(cells):
            at=next((row['t']/h for row in rows if row['q']>=scale*(j+1)/cells),1)
            cls=s.reveal(max(0,at-.035))
            glyph+=f'<rect x="{32+j*27}" y="12" width="21" height="25" rx="3" fill="#e7eef7"/><rect class="{cls}" x="{32+j*27}" y="12" width="21" height="25" rx="3" fill="{col}"/>'
        glyph+=f'<text x="32" y="65">도식 전체 = {fmt(scale)}건 (자체 눈금)</text>'
        body+=s.svg(glyph,'대기 공간 누적 도식',80)
        body+=s.metrics([('잔여 대기',fmt(q)+'건','동일 관찰 시점'),('누적 거부',fmt(rej)+'건','수지에서 계산')])
        parts.append(s.panel(title,body,summary='누적 처리 '+fmt(out)+'건'))
        s.table(title+' 수지',['관찰 s','유입','처리','거부','잔여'],[[r['t'],r['incoming'],r['served'],r['rejected'],r['q']] for r in rows[::10]])
    overload_arrivals=p['after_rate']*(h-p['change_time']);fraction=b['rejected']/overload_arrivals if overload_arrivals else 0
    s.numeric['overload_rejection_fraction']=fraction
    diagram='<path class="mr-rail" d="M45 68 H240 H440 M240 68 L370 135"/>'+s.box(4,38,92,56,'유입')+s.box(184,38,112,56,'버퍼',f'상한 {fmt(limit)}')+s.box(391,38,105,56,'처리')+s.box(332,112,152,50,'초과 거부',color=R)
    diagram+=s.token_stream(98,68,183,68,0,1,12)+s.token_stream(298,68,389,68,0,1,8,G)+s.token_stream(240,98,365,110,.45,.98,9,R)
    return s.stack(s.grid(*parts),s.panel('상한에서 초과분을 빠르게 거부',s.svg(diagram,'버퍼 상한과 초과 요청의 거부 경로',180),'이동 점은 상징 표현',f'과부하 구간 유입 {fmt(overload_arrivals)}건 중 거부 {fmt(b["rejected"])}건 = {fraction*100:.2f}%')),phase((0,'같은 조건','유입량과 처리 한도는 좌우가 같다.'),(p['change_time']/h,'과부하 지속','상한 없는 큐는 계속 늘고, 제한된 큐는 초과분을 거부한다.'),(.85,'성공과 거부를 함께 본다','대기를 제한한 효과와 거부한 요청의 비용을 동시에 기록한다.'))

def cache(s,p):
    total=finite(p['requests_per_second'],'requests_per_second',1);normal=finite(p['normal_hit_percent'],'normal_hit_percent',0,100);low=finite(p['minimum_hit_percent'],'minimum_hit_percent',0,normal)
    hit=samples(lambda t:piece(t,[(0,normal),(.4,normal),(.42,low),(.56,low),(.78,normal),(1,normal)]),101)
    qps=[[t,total*(1-v/100)] for t,v in hit]
    s.numeric.update(hit=hit,qps=qps,total=total)
    c=s.grid(s.chart('캐시 히트율',[('HIT',hit,G)],'%',100,[(.4,'TTL 만료',A),(.78,'회복',G)]),s.chart('미스에서 파생된 DB 요청',[('DB',qps,P)],'QPS',total*1.1,[(.4,'미스 증가',R)],x_label='총 요청 일정'))
    return s.stack(c,split_diagram(s,'cache'),s.metrics([('총 요청',fmt(total)+'/s','일정하다는 가정'),('정상 DB 요청',fmt(total*(1-normal/100))+'/s','미스율 × 총 요청'),('최대 DB 요청',fmt(total*(1-low/100))+'/s','미스당 DB 요청 1회')])),phase((0,'캐시의 보호','대부분이 HIT이므로 DB는 미스만 받는다.'),(.4,'동시 미스','같은 키의 만료가 DB 경로로 요청을 집중시킨다.'),(.78,'회복과 완화','재계산 중복 억제·만료 분산 등의 정책은 별도 조건을 검증한다.'))

def timeout(s,p):
    gw=finite(p['gateway_timeout'],'gateway_timeout',.1,60);be=finite(p['backend_duration'],'backend_duration',gw+.01,90);h=finite(p['horizon'],'horizon',be,120)
    X=lambda t:70+390*t/h
    run1=s.track([(0,'width:0px'),(gw/h,f'width:{390*gw/h}px'),(1,f'width:{390*gw/h}px')])
    run2=s.track([(0,'width:0px'),(be/h,f'width:{390*be/h}px'),(1,f'width:{390*be/h}px')])
    body=f'<text x="60" y="34" text-anchor="end">GW</text><text x="60" y="114" text-anchor="end">BE</text><rect x="70" y="15" width="390" height="35" rx="5" fill="#edf2f8"/><rect x="70" y="95" width="390" height="35" rx="5" fill="#edf2f8"/><rect class="{run1}" x="70" y="15" width="{390*gw/h}" height="35" rx="5" fill="{R}"/><rect class="{run2}" x="70" y="95" width="{390*be/h}" height="35" rx="5" fill="{B}"/>'
    abandon=s.reveal(gw/h)
    body+=f'<g class="{abandon}"><rect x="{X(gw)}" y="91" width="{X(be)-X(gw)}" height="43" fill="#f4ce7e" opacity=".6"/><text x="{(X(gw)+X(be))/2}" y="160" text-anchor="middle">대기자 없음</text></g>'
    for at,label,y,color in [(gw,'504',73,R),(be,'200',189,G)]:
        cls=s.reveal(at/h)
        body+=f'<g class="{cls}"><line x1="{X(at)}" x2="{X(at)}" y1="5" y2="205" stroke="{color}" stroke-dasharray="5 4"/><text x="{X(at)}" y="{y}" text-anchor="middle" style="fill:{color}">{fmt(at)}s · {label}</text></g>'
    body+='<text x="70" y="229">0s</text>'+f'<text x="460" y="229" text-anchor="end">{fmt(h)}s</text>'
    s.numeric.update(gateway_timeout=gw,backend_duration=be,unobserved_work=be-gw,request_count=1)
    s.table('단일 요청 결과',['관찰자','결과','시점 s'],[['사용자/게이트웨이','504',gw],['백엔드','200 (응답 미수신)',be]])
    gw_expired=s.reveal(gw/h);be_done=s.reveal(be/h)
    network='<path class="mr-rail" d="M94 57 H204 M306 57 H406"/>'+s.box(3,28,92,58,'사용자')+s.box(204,28,102,58,'GW')+s.box(406,28,90,58,'BE')
    network+=f'<g class="{gw_expired}"><path d="M204 105 H98 l12 -6 m-12 6 l12 6" fill="none" stroke="{R}" stroke-width="3"/><text x="155" y="133" text-anchor="middle">504</text></g>'
    network+=f'<g class="{be_done}"><path d="M406 105 H333 l12 -6 m-12 6 l12 6" fill="none" stroke="{G}" stroke-width="3"/><path d="M312 96 l16 18 m0 -18 l-16 18" stroke="{R}" stroke-width="3"/><text x="371" y="133" text-anchor="middle">200 · 폐기</text></g>'
    return s.stack(s.panel('계층별 결과 경로',s.svg(network,'사용자에게는504, 백엔드에서는200이 기록되는 서로 다른 경로',155)),s.panel('서로 다른 대기 예산',s.svg(body,'게이트웨이는 먼저 대기를 끝내지만 백엔드는 계속 수행',245),'GW = Gateway · BE = Backend'))+s.metrics([('사용자 결과','504',f'{gw:g}초에 대기 종료'),('백엔드 결과','200',f'{be:g}초에 완료'),('대기자 없는 실행',f'{be-gw:g}초','취소가 전파되지 않은 가정')]),phase((0,'하나의 요청','전송 시간은 생략하고 같은 원점에서 시작한다.'),(gw/h,'게이트웨이 종료','사용자는 오류를 받았지만 백엔드는 아직 실행 중이다.'),(be/h,'늦은 완료','백엔드의 성공 기록이 사용자 성공을 뜻하지 않는다.'))

def slow(s,p):
    v1=finite(p['week1'],'week1',0,10000);v4=finite(p['week4'],'week4',v1+.001,10000);threshold=finite(p['threshold'],'threshold',v4,20000)
    baseline=lambda t:v1+(v4-v1)*t
    raw=samples(lambda t:baseline(t)+18*math.sin(t*2*math.pi*28)+6*math.sin(t*2*math.pi*56),225)
    upper=max(threshold,max(v for _,v in raw))*1.1
    c=s.chart('4주 P99 추세',[('현재',raw,B)],'ms',upper,threshold=threshold,x_label='4주 관찰',x_ticks=[(0,'1주'),(1/3,'2주'),(2/3,'3주'),(1,'4주')])
    overlay=s.chart('같은 요일 패턴 비교',[('1주',samples(lambda t:v1+20*math.sin(t*math.pi*14)),G),('4주',samples(lambda t:v4+20*math.sin(t*math.pi*14)),R)],'ms',upper,x_label='요일 정렬',x_ticks=[(0,'월'),(.5,'목'),(1,'일')])
    growth=(v4-v1)/v1*100 if v1 else None
    s.numeric.update(week1=v1,week4=v4,growth_percent=growth)
    return s.stack(c,overlay,s.metrics([('첫 구간 대표값',fmt(v1)+'ms','합성 비교 기준'),('마지막 대표값',fmt(v4)+'ms','동일 조건 가정'),('상대 변화',('정의 불가' if growth is None else f'+{growth:.2f}%'),'원점 대표값 대비')])),phase((0,'알람이 없을 수 있다','임계치 아래에서도 느려지는 추세가 쌓인다.'),(.5,'조건을 맞춘 비교','같은 요일과 트래픽 조건을 맞춘다는 가정을 확인한다.'),(.85,'침식을 드러낸다','미래를 확정 예측하지 않고 관찰된 변화량을 계산한다.'))

def deploy(s,p):
    first=lambda t:piece(t,[(0,80),(.25,80),(.31,220),(.62,95),(1,85)])+2*math.sin(50*t)
    second=lambda t:piece(t,[(0,80),(.25,80),(.31,245),(.75,310),(.84,85),(1,80)])+2*math.sin(50*t)
    a=s.chart('A · 워밍업 이후 회복',[('P99',samples(first),B)],'ms',360,[(.25,'배포',P)],x_label='배포 전후 합성 관찰')
    b=s.chart('B · 악화 후 롤백',[('P99',samples(second),R)],'ms',360,[(.25,'배포',P),(.75,'롤백',G)],x_label='배포 전후 합성 관찰')
    return s.grid(a,b),phase((0,'기준 구간','두 예시의 배포 전 상태와 같은 축을 확인한다.'),(.25,'배포 직후 변화','일시적인 상승과 지속 악화를 구분한다.'),(.57,'회복 방향 비교','A는 내려오고 B는 높은 수준을 유지한다.'),(.8,'변경 뒤 확인','롤백 이후의 회복은 이 시나리오의 결과이지 모든 장애의 보장은 아니다.'))

def postmortem(s,p):
    times=[p[x] for x in ['first','alert','response','recovery']];h=finite(p['horizon'],'horizon',1,300)
    if not 0<times[0]<times[1]<times[2]<times[3]<h:raise ValueError('Incident timestamps must be ordered')
    for value in times:
        finite(value,'event minute',0,h)
        if value!=int(value):raise ValueError('Use integer minute timestamps')
    f,a,r,z=times
    fn=lambda t:piece(t,[(0,70),(f/h,75),(a/h,300),(.62,550),(z/h,550),((z+1)/h,75),(1,75)])
    stamp=lambda m:f'{2+int(m)//60:02d}:{int(m)%60:02d}'
    events=[(t/h,stamp(t),col) for t,col in zip(times,[A,R,P,G])]
    c=s.chart('P99와 네 사건',[('P99',samples(fn,181),B)],'ms',700,events,threshold=300,x_label='사건 관찰 시각',x_ticks=[(0,'02:00'),(1/3,stamp(h/3)),(2/3,stamp(h*2/3)),(1,stamp(h))])
    intervals=[('감지 공백',f,a,A),('알림 → 복구',a,z,B),('알림 → 대응 시작',a,r,P),('대응 시작 → 복구',r,z,G)]
    s.numeric['intervals']={name:end-start for name,start,end,color in intervals}
    body=''
    for i,(name,start,end,color) in enumerate(intervals):
        y=25+i*49;x=70+380*start/h;width=380*(end-start)/h;cls=s.reveal(.55+i*.08)
        body+=f'<g class="{cls}"><line x1="70" x2="450" y1="{y+10}" y2="{y+10}" stroke="#e1e9f2"/><rect x="{x}" y="{y}" width="{width}" height="12" rx="4" fill="{color}"/><text x="70" y="{y+34}">{esc(name)} · {fmt(end-start)}분</text></g>'
    s.table('사건 시각',['사건','시각'],list(zip(['첫 흔적','알림','대응 시작','복구'],[stamp(t) for t in times])))
    return s.stack(c,s.panel('간격을 계산한다',s.svg(body,'감지와 대응 각 구간의 시간 차이',228))),phase((0,'그래프를 다시 본다','복구된 이후 전체 경과를 재구성한다.'),(.38,'사건을 정렬한다','첫 흔적·알림·대응 시작·복구를 구분해 놓는다.'),(.84,'두 시간을 더 잘게 나눈다','알림부터 복구까지와 실제 대응을 시작한 이후의 시간은 다르다.'))

def gc_pause(s,p):
    events=[.22,.47,.72,.92]
    def heap(t):
        cuts=[0]+events+[1]
        for a,b in zip(cuts,cuts[1:]):
            if a<=t<b:return 28+58*(t-a)/(b-a)
        return 28
    latency=lambda t:70+480*max(math.exp(-((t-e)/.007)**2) for e in events)
    charts=s.grid(s.chart('P99 스파이크',[('P99',samples(latency,301),P)],'ms',600,[(e,'GC',R) for e in events]),s.chart('GC 사건과 힙',[('힙',sorted(samples(heap,301)+[[e-0.00001,heap(e-0.00001)] for e in events]+[[e,heap(e)] for e in events if all(abs(e-i/300)>1e-9 for i in range(301))]),B)],'%',100,[(e,'정지',R) for e in events]))
    return charts,phase((0,'보너스 케이스','배포 코드에는 있지만 현재 본문에 삽입되지 않은 데모를 별도로 다룬다.'),(.45,'시각을 맞춘다','지연 스파이크와 GC 이벤트가 같은 시간에 놓이도록 한다.'),(.85,'추가 로그로 검증한다','시간 정렬은 가설을 돕는다. 실제 정지 로그를 확인해야 한다.'))

# ---- live runtime cases (inline JS + SVG; see references/live-runtime.md) ----

CAPTION_CPS=12.0      # reading speed assumed for Korean captions (chars per second)
CAPTION_MIN_S=2.5     # minimum wall seconds any caption stays on screen
CAPTION_MAX_CHARS=50  # longer captions are a writing problem, not a pacing problem
DEFAULT_SPEED=1.25

def caption_need(text):return max(CAPTION_MIN_S,len(text)/CAPTION_CPS)

def rate_at(rate,t):
    r=1
    for x in rate:
        if t>=x[0]-1e-9:r=x[1]
    return r

def caption_walls(captions,rate,end,speed=DEFAULT_SPEED):
    """Wall seconds each caption is on screen during one play (last caption: until the end)."""
    caps=sorted(captions,key=lambda c:c[0]);pts=sorted({0.0,end}|{x[0] for x in rate if 0<=x[0]<=end}|{c[0] for c in caps});out=[]
    for i,c in enumerate(caps):
        a=c[0];b=caps[i+1][0] if i+1<len(caps) else end
        out.append(sum((y-x)/(rate_at(rate,x)*speed) for x,y in zip(pts,pts[1:]) if x>=a-1e-9 and y<=b+1e-9))
    return out

def paced_rate(captions,end,base,speed=DEFAULT_SPEED,floor=0.12):
    """Playback-rate map: `base` (model-time pacing) slowed wherever a caption would otherwise
    disappear before it can be read. Raises when captions are too close to be read at all."""
    caps=sorted(captions,key=lambda c:c[0])
    for c in caps:
        if len(c[2])>CAPTION_MAX_CHARS:raise ValueError(f'Caption longer than {CAPTION_MAX_CHARS} chars: {c[2]}')
    pts=sorted({0.0,end}|{x[0] for x in base if 0<=x[0]<=end}|{c[0] for c in caps});out=[]
    for i,c in enumerate(caps):
        a=c[0];b=caps[i+1][0] if i+1<len(caps) else end
        segs=[(x,y,rate_at(base,x)) for x,y in zip(pts,pts[1:]) if x>=a-1e-9 and y<=b+1e-9]
        need=caption_need(c[2]) if i+1<len(caps) else 0
        wall=sum((y-x)/(r*speed) for x,y,r in segs)
        if need and wall<=1e-9:raise ValueError(f'Caption {c[1]} has no time on screen; merge it with the next one')
        k=1 if wall>=need else wall/need
        for x,y,r in segs:
            if r*k<floor:raise ValueError(f'Caption {c[1]} needs a playback rate below {floor}; merge or move captions')
            out.append([round(x,4),math.floor(r*k*1e4)/1e4])   # round down: never shorter than needed
    merged=[]
    for x in out:
        if not merged or abs(merged[-1][1]-x[1])>1e-9:merged.append(x)
    return merged
def nice_ceiling(v,step):return max(step,math.ceil(v/step-1e-9)*step)

def pool_live_data(p):
    """Model -> data for the live thread-pool scene. Captions and playback pacing are
    bound to model events (queue onset, drain), never to fixed fractions of the clip."""
    jobs=pool_model(p);w=p['workers'];h=p['horizon'];dt=0.05;n=int(round(h/dt))
    states=[pool_state(jobs,i*dt) for i in range(n+1)]
    active=[s['active'] for s in states];queued=[s['queued'] for s in states]
    win=max(1,round(p['arrival_interval']/dt))
    smooth=[round(sum(queued[max(0,i-win+1):i+1])/len(queued[max(0,i-win+1):i+1]),3) for i in range(n+1)]
    waits=[j for j in jobs if j['wait']>1e-9]
    q_max=max(queued);t_qmax=queued.index(q_max)*dt if q_max else None
    t_queue=min(j['arrive'] for j in waits) if waits else None
    t_drain=max(j['start'] for j in waits) if waits else None
    resp=[j['end']-j['arrive'] for j in jobs];max_job=max(range(len(jobs)),key=lambda i:(round(resp[i],9),-i))
    ns,ss,s0,s1=p['normal_service'],p['slow_service'],p['slow_start'],p['recovery']
    rate=1/p['arrival_interval'];need_n=ns*rate;need_s=ss*rate
    f1=lambda v:f'{v:.1f}';fg=lambda v:f'{v:g}';fn=lambda v:f'{round(v,1):g}'
    captions=[[0,'①',f'평소엔 요청이 {fg(ns)}초면 끝나 {w}칸 중 {fn(need_n)}칸만 쓴다.'],
              [s0,'②',f'{fg(s0)}초, DB가 느려져 처리 시간이 {fg(ss)}초로 늘었다.']]
    if t_queue is not None:
        captions.append([t_queue,'③',f'{w}칸이 다 차자 새 요청이 줄을 서기 시작한다.'])
    end_at=max(s1,(t_drain or s1))+0.3
    if t_queue is not None:
        captions.append([s1,'④',f'{fg(s1)}초에 DB가 회복돼도 시작한 작업이 끝나야 줄이 빠진다.'])
        captions.append([min(end_at,h),'⑤',f'트래픽은 그대로였다. 필요한 칸({fn(need_s)})이 {w}칸을 넘었을 뿐이다.'])
    else:   # no queue: recovery and conclusion are one claim (two captions 0.3 s apart cannot both be read)
        captions.append([s1,'③',f'{fg(s1)}초, DB 회복. 칸이 남아 줄 없이 응답만 늘었었다.'])
    captions.sort(key=lambda c:c[0])
    # Pacing: slow down from the incident until the queue is visible, speed past the tail;
    # paced_rate then guarantees reading time for every caption.
    rate_map=paced_rate(captions,h,[[0,1.1],[s0,0.5],[min(s1,(t_queue if t_queue is not None else s0+1.2)+0.4),1.0],[s1,0.8],[min(h,end_at),1.5]])
    stack_max=nice_ceiling((w+q_max)*1.2,4);rmax=nice_ceiling(max(resp)*1.05,2)
    data=dict(scene='thread-pool',
      params={k:p[k] for k in ['workers','arrival_interval','normal_service','slow_service','slow_start','recovery','horizon']},
      jobs=[[round(j['arrive'],6),round(j['start'],6),round(j['end'],6),j['slot'],j['service']] for j in jobs],
      series=dict(dt=dt,active=active,queued_smooth=smooth),
      events=dict(t_queue=t_queue,t_queue_max=t_qmax,q_max=q_max,t_drain=t_drain,max_job=max_job),
      captions=captions,rate=rate_map,
      axes=dict(stack_max=stack_max,response_max=rmax,response_ticks=[0,rmax/2,rmax],hot_response=max(1.0,ns*3),x_step=2 if h<=16 else 5),
      labels=dict(inflow=f'유입 {f1(rate)}건/s',pool='스레드 풀',dependency='DB',slow_band=f'DB 지연 {fg(s0)}–{fg(s1)}초'))
    aria=(f'스레드 {w}칸 풀에 초당 {f1(rate)}건이 들어온다. {fg(s0)}초에 처리 시간이 {fg(ns)}초에서 {fg(ss)}초로 늘자 '
          +(f'풀이 모두 차고 대기열이 최대 {q_max}건까지 쌓이며 체감 응답 시간이 최대 {f1(resp[max_job])}초로 뛴다. '
            f'{fg(s1)}초에 회복해도 이미 시작한 작업이 끝난 뒤에야 대기열이 빠진다.' if waits else '대기열은 생기지 않는다.'))
    notes=(f'결정론적 FIFO 모델입니다. 스레드 {w}개, {fg(p["arrival_interval"])}초 간격 도착({len(jobs)}건), 처리 시간은 시작 시각 기준 '
           f'평소 {fg(ns)}초, {fg(s0)}~{fg(s1)}초 시작분 {fg(ss)}초. 처리 시간은 DB 응답 시간으로 단순화했고 가로축은 모델 시간입니다. '
           '재생은 장애 전환 구간을 느리게, 회복 이후를 빠르게 보여줍니다.'+(' 대기 영역은 도착 간격 이동평균이며, 최대 대기 수치는 이동평균 전 원값입니다.' if waits else ''))
    table=(['요청','도착','시작','완료','슬롯','대기','응답'],[[j['id'],f"{j['arrive']:.2f}",f"{j['start']:.2f}",f"{j['end']:.2f}",j['slot']+1,f"{j['wait']:.2f}",f"{j['end']-j['arrive']:.2f}"] for j in jobs])
    numeric=dict(jobs=jobs,states=[(i*dt,s) for i,s in enumerate(states) if i%4==0],max_queue=q_max,live=dict(t_queue=t_queue,t_drain=t_drain,max_response=resp[max_job]))
    return data,aria,notes,table,numeric

def nice_max(v):
    """Smallest 1/1.2/1.5/2/2.5/3/4/5/6/8 x 10^k that is >= v (axis ceilings)."""
    if v<=0:return 1
    e=10**math.floor(math.log10(v))
    return next(m*e for m in (1,1.2,1.5,2,2.5,3,4,5,6,8,10) if m*e>=v-1e-9)

def grp(v):return f'{round(v):,}'

def interp(ts,vs,t):
    if t<=ts[0]:return vs[0]
    for i in range(1,len(ts)):
        if t<=ts[i]:
            span=ts[i]-ts[i-1] or 1;return vs[i-1]+(vs[i]-vs[i-1])*(t-ts[i-1])/span
    return vs[-1]

def first_reach(ts,vs,level):
    """First time a non-decreasing piecewise-linear series reaches level, or None."""
    if vs[0]>=level-1e-9:return ts[0]
    for i in range(1,len(ts)):
        if vs[i]>=level-1e-9:
            span=vs[i]-vs[i-1];return ts[i] if span<=0 else ts[i-1]+(ts[i]-ts[i-1])*(level-vs[i-1])/span
    return None

def fluid_series(rows):
    return dict(t=[round(r['t'],6) for r in rows],q=[round(r['q'],6) for r in rows],inc=[round(r['incoming'],6) for r in rows],
                srv=[round(r['served'],6) for r in rows],rej=[round(r['rejected'],6) for r in rows])

def token_unit(rate,most=30):
    """Requests per drawn token, so the busiest stream draws at most `most` tokens/s."""
    return next(u for u in (1,2,5,10,20,50,100,200,500,1000,2000,5000,10000) if rate/u<=most+1e-9)

def fluid_tokens(series,unit):
    """Each token = `unit` requests: arrival when cumulative inflow crosses k*unit; a token is
    rejected when accepted inflow has not grown by a further unit; an accepted token leaves
    the queue (FIFO) when cumulative service crosses its accepted index * unit."""
    ts,inc,srv,rej=series['t'],series['inc'],series['srv'],series['rej'];out=[];accepted=0;k=1
    while k*unit<=inc[-1]+1e-9:
        ta=first_reach(ts,inc,k*unit);acc=interp(ts,inc,ta)-interp(ts,rej,ta)
        if math.floor(acc/unit+1e-6)<accepted+1:out.append([round(ta,4),None,1])
        else:
            accepted+=1;tsv=first_reach(ts,srv,accepted*unit)
            out.append([round(ta,4),None if tsv is None else round(max(ta,tsv),4),0])
        k+=1
    return out

def token_speed(peak_rate,unit,spacing=15):
    """Token speed in px/s so that tokens of the busiest stream sit ~`spacing` px apart."""
    return max(240,round(spacing*peak_rate/unit))

def live_rate_map(points,h):
    out=[];last=-1
    for t,r in points:
        t=min(max(0,t),h)
        if t>last+1e-9:out.append([round(t,4),r]);last=t
    return out

def pipeline_live_data(p):
    for key in ['gateway_capacity','database_capacity']:finite(p[key],key,.001)
    if not p['before_rate']<=p['application_capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    if p['gateway_capacity']<max(p['before_rate'],p['after_rate']) or p['database_capacity']<p['application_capacity']:
        raise ValueError('This example assumes only Application is the bottleneck')
    h=p['horizon'];rows=fluid_queue(p,steps=max(20,min(400,round(h/.05))));S=fluid_series(rows)
    before,after,cap,c0=p['before_rate'],p['after_rate'],p['application_capacity'],p['change_time']
    gw,db=p['gateway_capacity'],p['database_capacity'];unit=token_unit(after);qend=S['q'][-1]
    t1=first_reach(S['t'],S['q'],cap);t2=first_reach(S['t'],S['q'],2*cap)
    captions=[[0,'①',f'평소 {grp(before)}건/s는 Application 한도 {grp(cap)}건/s 안이다.'],
              [c0,'②',f'{c0:g}초, 트래픽이 {grp(after)}건/s로 늘었다.']]
    if t1 is not None:captions.append([t1,'③',f'한도를 넘는 {grp(after-cap)}건/s가 Application 앞에 쌓인다.'])
    if t2 is not None:captions.append([t2,'④','Gateway와 DB는 오히려 여유가 있다. 병목은 한 곳이다.'])
    captions.append([h,'⑤' if t2 is not None else '④',f'{h:g}초 뒤 대기 {grp(qend)}건, 새 요청은 {qend/cap:.1f}초를 기다린다.'])
    rate=paced_rate(captions,h,[[0,1.2],[c0-.5,.6],[(t1 or c0)+.5,1.0],[(t2 or c0+1)+.8,1.5]])
    data=dict(scene='pipeline-bottleneck',params={k:p[k] for k in ['before_rate','after_rate','gateway_capacity','application_capacity','database_capacity','change_time','horizon']},
      series=dict(t=S['t'],q=S['q'],srv=S['srv']),tokens=fluid_tokens(S,unit),unit=unit,speed=token_speed(after,unit),
      events=dict(t_change=c0,t_wait1=t1,t_wait2=t2,q_end=qend),captions=captions,rate=rate,
      axes=dict(q_max=nice_max(max(1,qend)),x_step=2 if h<=16 else 5),
      labels=dict(unit=f'점 1개 = 요청 {grp(unit)}건 · 한도 단위 건/s',source='Gateway',server='Application',server_short='App',dependency='DB'))
    aria=(f'Gateway, Application, DB 순서의 파이프라인. {c0:g}초에 유입이 {grp(before)}에서 {grp(after)}건/s로 늘자 한도 {grp(cap)}건/s인 '
          f'Application 앞에 매초 {grp(after-cap)}건씩 대기가 쌓여 {h:g}초에 {grp(qend)}건이 된다. DB는 한도 {grp(db)}건/s 중 {grp(cap)}건/s만 받는다.')
    notes=(f'결정론적 유체 모델입니다. 유입 {grp(before)}→{grp(after)}건/s({c0:g}초 변경), Gateway·Application·DB 한도 {grp(gw)}·{grp(cap)}·{grp(db)}건/s. '
           f'대기는 구간별 수지(유입−처리)로 적분했고, 점 1개는 요청 {grp(unit)}건입니다. 점의 도착·출발 시각은 누적 유입·누적 처리 곡선에서 계산합니다. '
           '새 요청 대기 시간 = 대기 ÷ Application 한도(FIFO, 한도 일정 가정). 가로축은 모델 시간입니다.')
    table=(['시각','누적 유입','누적 처리','대기'],[[f"{r['t']:g}",grp(r['incoming']),grp(r['served']),grp(r['q'])] for r in rows if abs(r['t']-round(r['t']))<1e-9])
    numeric=dict(rows=rows[::10]+[rows[-1]],final=rows[-1],live=dict(unit=unit,tokens=len(data['tokens']),t_wait1=t1,t_wait2=t2))
    return data,aria,notes,table,numeric

def bounded_live_data(p):
    limit=finite(p['queue_limit'],'queue_limit',.001,1000)
    if not p['before_rate']<=p['capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    h=p['horizon'];steps=max(20,min(400,round(h/.05)))
    U=fluid_series(fluid_queue(p,steps=steps));Bq=fluid_series(fluid_queue(p,limit,steps=steps))
    before,after,cap,c0=p['before_rate'],p['after_rate'],p['capacity'],p['change_time'];unit=token_unit(after)
    t_full=first_reach(Bq['t'],Bq['q'],limit);t_wait=first_reach(U['t'],U['q'],cap)
    served=Bq['srv'][-1];rej=Bq['rej'][-1];over=Bq['inc'][-1]-interp(Bq['t'],Bq['inc'],c0);frac=rej/over*100 if over else 0
    captions=[[0,'①',f'두 큐 모두 유입 {grp(before)}건/s, 처리 한도 {grp(cap)}건/s다.']]
    if t_full is not None:captions.append([t_full,'②',f'{c0:g}초, 유입 {grp(after)}건/s. 상한 큐는 {limit:g}건을 넘는 요청을 거부한다.'])
    if t_wait is not None:captions.append([t_wait,'③','상한 없는 큐는 계속 쌓여 새 요청이 1초 넘게 기다린다.'])
    captions.append([h,'④',f'처리량은 둘 다 {grp(served)}건. 상한은 대기를 거부로 바꿀 뿐이다.'])
    rate=paced_rate(captions,h,[[0,1.2],[c0-.5,.6],[(t_wait or c0)+.4,1.0],[(t_wait or c0+1)+1.5,1.5]])
    data=dict(scene='bounded-queue',params={k:p[k] for k in ['before_rate','after_rate','capacity','queue_limit','change_time','horizon']},
      series=dict(t=U['t'],qu=U['q'],qb=Bq['q'],srv=Bq['srv'],rej=Bq['rej'],inc=Bq['inc']),
      tokens_u=fluid_tokens(U,unit),tokens_b=fluid_tokens(Bq,unit),unit=unit,speed=token_speed(after,unit),
      events=dict(t_change=c0,t_full=t_full,t_wait1=t_wait),captions=captions,rate=rate,
      axes=dict(q_max=nice_max(max(1,U['q'][-1])),wait_max=nice_max(max(1,U['q'][-1]/cap)),x_step=2 if h<=16 else 5),
      labels=dict(unit=f'점 1개 = 요청 {grp(unit)}건 · 상한 칸 1개 = 1건 · 아래 선 = 대기 시간',lane_u='상한 없음 (무한 큐)',lane_b=f'상한 {limit:g}건 + 즉시 거부',server='서버',
                  limit=f'상한 {limit:g}',pill_u='대기 시간 계속 증가',pill_b=f'수용분 대기 {limit/cap*1000:.0f}ms'))
    if abs(U['srv'][-1]-served)>1e-6:raise ValueError('Both queues are expected to serve the same amount')
    aria=(f'같은 유입과 처리 한도 {grp(cap)}건/s의 두 큐. {c0:g}초에 유입이 {grp(after)}건/s로 늘자 상한 없는 큐는 {h:g}초에 대기 {grp(U["q"][-1])}건까지 쌓이고, '
          f'상한 {limit:g}건 큐는 대기를 {limit:g}건으로 유지하며 {grp(rej)}건을 거부한다. 두 큐의 처리량은 {grp(served)}건으로 같다.')
    notes=(f'결정론적 유체 모델입니다. 처리 한도 {grp(cap)}건/s, 유입 {grp(before)}→{grp(after)}건/s({c0:g}초 변경), 버퍼 상한 {limit:g}건. '
           f'두 큐의 대기 막대는 같은 건수 눈금입니다. 점 1개는 요청 {grp(unit)}건이며, 도착·거부·출발 시각은 누적 곡선에서 계산합니다. '
           f'새 요청 대기 시간 = 대기 ÷ 처리 한도(FIFO). 거부율 = 누적 거부 ÷ 과부하 구간 유입({grp(over)}건).')
    table=(['시각','유입','처리','대기(상한 없음)','대기(상한)','거부'],[[f"{t:g}",grp(i),grp(s_),grp(qu),f'{qb:g}',grp(r)] for t,i,s_,qu,qb,r in zip(U['t'],Bq['inc'],Bq['srv'],U['q'],Bq['q'],Bq['rej']) if abs(t-round(t))<1e-9])
    numeric=dict(final_unbounded=U['q'][-1],final_bounded=Bq['q'][-1],rejected=rej,served=served,overload_rejection_fraction=frac/100,live=dict(unit=unit,t_full=t_full,t_wait1=t_wait))
    return data,aria,notes,table,numeric

def cpu_live_data(p):
    """Three synthetic CPU/P99 pairs on a 60 s synthetic axis; verdicts bound to knot events."""
    H=60.0;n=240;sc=cpu_scenarios();ts=[round(i*H/n,6) for i in range(n+1)]
    ser=lambda fn:[round(fn(t/H),3) for t in ts]
    b,c=sc[1],sc[2];E={k:v*H for k,v in {**b['events'],**c['events']}.items()}
    early=max(max(ser(x['p99'])[:int(n*min(E.values())/H)+1]) for x in sc)
    b_cpu=sum(ser(b['cpu']))/(n+1);b_peak=b['p99'](1)
    services=[dict(cpu=ser(x['cpu']),p99=ser(x['p99'])) for x in sc]
    # Pattern names and readings appear only once the event that justifies them has happened.
    services[0].update(pill=[[0,'① 건강한 상태','ok']],note=[[E['cpu_rise'],'CPU는 부하를 따르고 응답은 안정','ok']])
    services[1].update(pill=[[0,'②','info'],[E['p99_plateau'],'② CPU는 노는데 느리다','warn']],note=[[E['p99_plateau'],'I/O·락·풀 대기를 의심','warn']])
    services[2].update(pill=[[0,'③','info'],[E['cpu_saturated'],'③ CPU 100%에 붙었다','hot']],note=[[E['cpu_saturated'],'연산 병목 또는 무한 루프를 의심','hot']])
    summary=E['p99_plateau']+.15*H
    captions=[[0,'①','세 서비스의 CPU(위)와 P99(아래)를 같은 시각에 읽는다.'],
              [E['cpu_rise'],'②','세 번째 서비스는 CPU가 오르자 P99도 함께 오른다.'],
              [E['p99_rise'],'③',f'두 번째 서비스는 CPU {b_cpu:.0f}%인데 P99가 오르기 시작한다.'],
              [E['cpu_saturated'],'④','세 번째는 CPU 100%: 연산이 코어를 넘었다.'],
              [E['p99_plateau'],'⑤','두 번째는 CPU가 한가한데 느리다. 무언가를 기다린다.'],
              [summary,'⑥','CPU만 보면 두 번째는 정상처럼 보인다. P99와 함께 읽자.']]
    captions.sort(key=lambda x:x[0])
    rate=paced_rate(captions,H,[[0,3.0],[E['cpu_rise']-1,2.0],[E['p99_plateau']+2,2.6],[summary,4.0]])
    data=dict(scene='cpu-latency',services=services,series=dict(t=ts),events=E,captions=captions,rate=rate,
      axes=dict(end=H,p99_max=1000,x_ticks=[[0,'0'],[20,'20'],[40,'40'],[60,'60초']]),labels=dict(cpu='CPU 사용률',p99='P99 응답 시간'))
    aria=('세 서비스의 CPU 사용률과 P99 응답 시간을 같은 시간축에 위아래로 놓은 그림. A는 둘 다 평온하다. '
          f'C는 CPU가 100%로 오르며 P99도 오른다(연산 포화 의심). B는 CPU가 {b_cpu:.0f}% 근처인데 P99가 {b_peak:g}ms로 오른다(대기 의심).')
    notes=('설명용 합성값입니다. 가로축 60초는 읽기 편의를 위한 합성 시간이며, 사건 시각(C CPU 상승 12초·포화 24초, B P99 상승 21초·정점 36초)은 곡선의 꺾임점입니다. '
           'CPU–P99 조합은 원인 판정이 아니라 가설을 고르는 단서입니다. 판정 문구는 해당 사건 이후에만 나타납니다.')
    table=(['시각','A CPU','A P99','B CPU','B P99','C CPU','C P99'],[[f'{ts[i]:g}']+[f"{s[k][i]:.0f}" for s in services for k in ('cpu','p99')] for i in range(0,n+1,20)])
    numeric=dict(events=E,early_p99_max=early,b_cpu_mean=b_cpu,b_p99_peak=b_peak)
    return data,aria,notes,table,numeric

def _probe_pool(p):
    jobs=pool_model(p)
    def probe(t):
        s=pool_state(jobs,t);return dict(state=dict(used=s['active'],queued=s['queued']),stats=[str(s['active']),str(s['queued'])])
    return probe

def _probe_pipeline(p):
    S=pipeline_live_data(p)[0]['series']
    def probe(t):
        q=max(0,interp(S['t'],S['q'],t));i=next((k for k in range(1,len(S['t'])) if S['t'][k]>t+1e-9),len(S['t'])-1)
        rate=p['before_rate'] if t<p['change_time']-1e-9 else p['after_rate'];served=(S['srv'][i]-S['srv'][i-1])/(S['t'][i]-S['t'][i-1])
        return dict(state=dict(queue=round(q,1)),stats=[grp(rate),grp(served),f'{q/p["application_capacity"]:.1f}'])
    return probe

def _probe_bounded(p):
    S=bounded_live_data(p)[0]['series']
    def probe(t):
        return dict(state=dict(queue_unbounded=round(max(0,interp(S['t'],S['qu'],t)),1),queue_bounded=round(max(0,interp(S['t'],S['qb'],t)),1),rejected=round(max(0,interp(S['t'],S['rej'],t)),1)),stats=[])
    return probe

def _probe_cpu(p):
    D=cpu_live_data(p)[0];ts=D['series']['t']
    def probe(t):
        return dict(state=dict(cpu=[round(interp(ts,s['cpu'],t),1) for s in D['services']],p99=[round(interp(ts,s['p99'],t),1) for s in D['services']]),stats=[])
    return probe

def live_checks(case_id,p):
    """Browser-gate inputs per live case: model probe at T, sample times, and annotations
    that must be absent just before and present just after their event time."""
    data=LIVE_BUILDERS[case_id](p)[0]
    if case_id=='thread-pool':
        ev=data['events'];jobs=pool_model(p);mj=jobs[ev['max_job']]
        samples=[.5,p['slow_start']+.6,(ev['t_queue'] or 5)+.5,ev['t_queue_max'] or 9,p['recovery']+1.5,p['horizon']]
        notes=[(l,a) for l,a in [('최대 대기',ev['t_queue_max']),(f"최대 {mj['end']-mj['arrive']:.1f}초",mj['end'])] if a is not None]
        return dict(probe=_probe_pool(p),samples=samples,annotations=notes,end=p['horizon'],resize_at=6.0)
    if case_id=='pipeline-bottleneck':
        ev=data['events'];c0=p['change_time']
        return dict(probe=_probe_pipeline(p),samples=[1.0,c0+.3,(ev['t_wait1'] or c0)+.2,(ev['t_wait2'] or c0)+.5,p['horizon']-1.3,p['horizon']],
                    annotations=[('한도 도달',c0+.06),('여유(한가함)',c0+.06)],end=p['horizon'],resize_at=c0+1.5)
    if case_id=='bounded-queue':
        ev=data['events'];c0=p['change_time']
        return dict(probe=_probe_bounded(p),samples=[1.0,c0+.04,(ev['t_full'] or c0)+.3,(ev['t_wait1'] or c0)+.3,p['horizon']-1.3,p['horizon']],
                    annotations=[(a,b) for a,b in [(data['labels']['pill_b'],ev['t_full']),(data['labels']['pill_u'],ev['t_wait1'])] if b is not None],end=p['horizon'],resize_at=c0+1.5)
    if case_id=='cpu-latency':
        E=data['events'];H=data['axes']['end']
        return dict(probe=_probe_cpu(p),samples=[3,E['cpu_rise']+2,E['p99_rise']+1.5,E['cpu_saturated']+2,E['p99_plateau']+3,H],
                    annotations=[('CPU 100%에 붙었다',E['cpu_saturated']),('CPU는 노는데 느리다',E['p99_plateau'])],end=H,resize_at=30.0)
    raise ValueError('No live checks for '+case_id)

LIVE_BUILDERS={'thread-pool':pool_live_data,'pipeline-bottleneck':pipeline_live_data,'bounded-queue':bounded_live_data,'cpu-latency':cpu_live_data}

BUILDERS={'traffic-patterns':traffic,'percentile-comparison':distributions,'survivorship-bias':survivorship,'cpu-latency':cpu,'cpu-throttling':throttling,'memory-leak':memory,'memory-spike':spike,'thread-pool':pool,'cluster-cascade':cascade,'event-loop':event_loop,'pipeline-bottleneck':pipeline,'utilization-wait':utilization,'bounded-queue':bounded,'cache-stampede':cache,'timeout-mismatch':timeout,'slow-degradation':slow,'deploy-comparison':deploy,'postmortem-timeline':postmortem,'gc-pause':gc_pause}

def build_case(meta,prefix=None,speed=1.25):
    from reference_scene import assemble
    if not isinstance(meta,dict) or meta.get('id') not in BUILDERS:raise ValueError('Unknown reference case')
    for key in ['title','goal','conclusion','assumptions']:
        value=meta.get(key)
        if not isinstance(value,str) or not value.strip() or len(value)>1500 or '{{' in value:raise ValueError('Invalid text: '+key)
    if not isinstance(meta.get('params'),dict):raise ValueError('params object required')
    # Allow only parameters already declared by the selected case's canonical contract.
    import json
    defaults=json.loads((__import__('reference_scene').ROOT/'examples/monitoring-cases.json').read_text())['cases']
    allowed=next(x['params'] for x in defaults if x['id']==meta['id'])
    if set(meta['params'])!=set(allowed):raise ValueError('Missing or unknown case parameters')
    if isinstance(speed,bool) or speed not in (1,1.25,1.5):raise ValueError('speed must be 1, 1.25 or 1.5')
    runtime=meta.get('runtime','css')
    if runtime not in ('css','live'):raise ValueError('runtime must be css or live')
    if runtime=='live':
        if meta['id'] not in LIVE_BUILDERS:raise ValueError('No live scene for this case')
        from live_scene import assemble_live
        prefix=prefix or 'ca-'+__import__('uuid').uuid4().hex[:12]
        data,aria,notes,table,numeric=LIVE_BUILDERS[meta['id']](meta['params'])
        return assemble_live(meta['id'],prefix,speed,data,meta['title']+'. '+aria,notes,table),numeric
    s=ReferenceScene(prefix);content,phases=BUILDERS[meta['id']](s,meta['params'])
    fragment=assemble(s,meta,content,phases,duration=18/speed)
    return fragment,s.numeric
