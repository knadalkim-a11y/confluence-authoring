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

# The three cases below are plain specs of the generic kinds in visual_spec (flow, trend):
# the monitoring pack is validation material for the same builder an author uses for any document.
def pipeline_spec(p):
    for key in ['gateway_capacity','database_capacity']:finite(p[key],key,.001)
    if not p['before_rate']<=p['application_capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    if p['gateway_capacity']<max(p['before_rate'],p['after_rate']) or p['database_capacity']<p['application_capacity']:
        raise ValueError('This example assumes only Application is the bottleneck')
    c0=p['change_time'];h=p['horizon']
    return dict(kind='flow',title='병목 앞에 쌓이고 뒤에는 여유가 남는다',claim='유입이 Application 한도를 넘으면 앞쪽에만 대기가 쌓인다.',
        source='원문의 600/300 req/s와 1000/800 한도, 정상 200·변경 시각·관찰 시간은 합성 가정',data_kind='example',
        time=dict(unit='초',end=h),units=dict(rate='건/s',count='건'),inflow=[[0,p['before_rate']],[c0,p['after_rate']]],
        stages=[dict(name='Gateway',capacity=p['gateway_capacity']),dict(name='Application',short='App',capacity=p['application_capacity']),dict(name='DB',capacity=p['database_capacity'])],
        labels=dict(inflow='트래픽',spare='여유(한가함)'),
        captions=[dict(at=0,text='평소 {inflow_start}건/s는 Application 한도 {capacity}건/s 안이다.'),
                  dict(at='change',text='{change}초, 트래픽이 {inflow_peak}건/s로 늘었다.'),
                  dict(at='wait:1',text='한도를 넘는 {excess}건/s가 Application 앞에 쌓인다.'),
                  dict(at='wait:2',text='Gateway와 DB는 오히려 여유가 있다. 병목은 한 곳이다.'),
                  dict(at='end',text='{end}초 뒤 대기 {queue_end}건, 새 요청은 {wait_end}초를 기다린다.')])

def bounded_spec(p):
    limit=finite(p['queue_limit'],'queue_limit',.001,1000)
    if not p['before_rate']<=p['capacity']<p['after_rate']:raise ValueError('Expected normal load below, overload above capacity')
    return dict(kind='flow',title='대기를 쌓을 것인가, 초과분을 거부할 것인가',claim='상한은 처리량을 늘리지 않고 넘치는 대기를 거부로 바꾼다.',
        source='결정론적 유체 모델, 서비스·과부하·버퍼 값은 입력값',data_kind='example',
        time=dict(unit='초',end=p['horizon']),units=dict(rate='건/s',count='건'),inflow=[[0,p['before_rate']],[p['change_time'],p['after_rate']]],
        stages=[dict(name='서버',capacity=p['capacity'])],
        variants=[dict(name='상한 없음 (무한 큐)',tone='bad',limit=None),dict(name=f'상한 {limit:g}건 + 즉시 거부',tone='good',limit=limit)],
        captions=[dict(at=0,text='두 큐 모두 유입 {inflow_start}건/s, 처리 한도 {capacity}건/s다.'),
                  dict(at='full@1',text='{change}초, 유입 {inflow_peak}건/s. 상한 큐는 {limit@1}건을 넘는 요청을 거부한다.'),
                  dict(at='wait:1',text='상한 없는 큐는 계속 쌓여 새 요청이 1초 넘게 기다린다.'),
                  dict(at='end',text='처리량은 둘 다 {served_end}건. 상한은 대기를 거부로 바꿀 뿐이다.')],
        callouts=[dict(lane=0,at='wait:1',text='대기 시간 계속 증가',tone='hot'),dict(lane=1,at='full@1',text='수용분 대기 {limit_wait_ms@1}ms',tone='ok')])

def cpu_spec(p):
    H=60.0;n=240;sc=cpu_scenarios();ts=[round(i*H/n,6) for i in range(n+1)]
    pts=lambda fn:[[t,round(fn(t/H),3)] for t in ts]
    E={k:v*H for k,v in {**sc[1]['events'],**sc[2]['events']}.items()}
    b_cpu=sum(sc[1]['cpu'](t/H) for t in ts)/(n+1);summary=E['p99_plateau']+.15*H
    early=max(max(v for t,v in pts(x['p99']) if t<=min(E.values())) for x in sc)
    panels=lambda x:[dict(label='CPU 사용률',unit='%',max=100,ticks=[100,50,0],decimals=0,series=[dict(name='CPU',color='blue',points=pts(x['cpu']))]),
                     dict(label='P99 응답 시간',unit='ms',max=1000,ticks=[1000,500,0],decimals=0,series=[dict(name='P99',color='purple',points=pts(x['p99']))])]
    return dict(kind='trend',title='CPU와 응답 시간을 함께 읽기',claim='CPU만 보면 두 번째는 정상처럼 보인다. P99와 함께 읽자.',
        source='설명용 합성값. 60초 축은 읽기 편의를 위한 합성 시간',data_kind='example',
        time=dict(unit='초',end=H,ticks=[[0,'0'],[20,'20'],[40,'40'],[60,'60초']]),
        groups=[dict(pill=[[0,'① 건강한 상태','ok']],note=[[E['cpu_rise'],'CPU는 부하를 따르고 응답은 안정','ok']],panels=panels(sc[0])),
                dict(pill=[[0,'②','info'],[E['p99_plateau'],'② CPU는 노는데 느리다','warn']],note=[[E['p99_plateau'],'I/O·락·풀 대기를 의심','warn']],panels=panels(sc[1])),
                dict(pill=[[0,'③','info'],[E['cpu_saturated'],'③ CPU 100%에 붙었다','hot']],note=[[E['cpu_saturated'],'연산 병목 또는 무한 루프를 의심','hot']],panels=panels(sc[2]))],
        captions=[dict(at=0,text='세 서비스의 CPU(위)와 P99(아래)를 같은 시각에 읽는다.'),
                  dict(at=E['cpu_rise'],text='세 번째 서비스는 CPU가 오르자 P99도 함께 오른다.'),
                  dict(at=E['p99_rise'],text=f'두 번째 서비스는 CPU {b_cpu:.0f}%인데 P99가 오르기 시작한다.'),
                  dict(at=E['cpu_saturated'],text='세 번째는 CPU 100%: 연산이 코어를 넘었다.'),
                  dict(at=E['p99_plateau'],text='두 번째는 CPU가 한가한데 느리다. 무언가를 기다린다.'),
                  dict(at=summary,text='CPU만 보면 두 번째는 정상처럼 보인다. P99와 함께 읽자.')]),dict(events=E,early_p99_max=early,b_cpu_mean=b_cpu)

def slow_spec(p):
    """SlowBurn: 4 weeks of P99 creeping up under the alert line; week 1 copied over week 4."""
    v1=finite(p['week1'],'week1',0,10000);v4=finite(p['week4'],'week4',v1+.001,10000);th=finite(p['threshold'],'threshold',v4,20000)
    W=4.0;n=224;f=lambda w:v1+(v4-v1)*w/W+18*math.sin(w/W*2*math.pi*28)+6*math.sin(w/W*2*math.pi*56)
    p99=[[round(i*W/n,5),round(f(i*W/n),3)] for i in range(n+1)]
    copy=[[round(3+i/56,5),round(f(i/56),3)] for i in range(57)]   # the first week's curve, laid over the fourth
    top=max(th*1.1,max(v for _,v in p99)*1.15)
    return dict(kind='trend',title='알람 없이 누적되는 성능 저하',claim='급락은 알람이 잡지만, 침식은 지난주와의 비교가 잡는다.',
        source='설명용 합성값. 4주 P99, 같은 트래픽 조건 가정',data_kind='example',
        time=dict(unit='주',end=W,ticks=[[.5,'1주차'],[1.5,'2주차'],[2.5,'3주차'],[3.5,'4주차']]),
        panels=[dict(label='P99 응답 시간 (4주)',unit='ms',max=round(top),ticks=[round(th),round(th/2),0],decimals=0,
                     series=[dict(name='P99',color='blue',points=p99),dict(name='1주차 곡선(복제)',color='green',points=copy)])],
        thresholds=[dict(panel='P99 응답 시간 (4주)',value=th,label=f'알람 임계선 {fmt(th)}ms')],
        between=[dict(panel='P99 응답 시간 (4주)',upper='P99',lower='1주차 곡선(복제)',**{'from':3,'to':4},color='red')],
        annotations=[dict(at=3.5,panel='P99 응답 시간 (4주)',series='P99',text='{P99_change_pct}% ({P99_start}ms → {P99_end}ms)',color='red',side='above')],
        captions=[dict(at=0,text='4주 동안 P99가 조금씩 오른다. 알람은 울리지 않는다.'),
                  dict(at=3,text='4주차에 1주차 곡선을 겹쳐 보면 차이가 보인다.'),
                  dict(at=3.6,text='급락은 알람이 잡지만, 침식은 지난주와의 비교가 잡는다.')]),dict(week1=v1,week4=v4,growth_percent=(v4-v1)/v1*100 if v1 else None)

def slow_live_data(p):
    sp,extra=slow_spec(p);d,a,n,t,num_,info=_from_spec(sp,'',extra)
    aria=(f"4주 동안의 P99 응답 시간. 대표값이 {fmt(extra['week1'])}ms에서 {fmt(extra['week4'])}ms로 오르지만 알람 임계선 {fmt(p['threshold'])}ms 아래라 알람은 없다. "
          f"4주차에 1주차 곡선을 겹치면 그 차이(+{extra['growth_percent']:.0f}%)가 드러난다.")
    return d,aria,n,t,num_

def postmortem_spec(p):
    """Postmortem: the recovery graph, four coloured events and the detection gap as a band."""
    f,a,r,z=[p[x] for x in ['first','alert','response','recovery']];h=finite(p['horizon'],'horizon',1,300)
    if not 0<f<a<r<z<h:raise ValueError('Incident timestamps must be ordered')
    fn=lambda m:piece(m/h,[(0,70),(f/h,75),(a/h,300),(.62,550),(z/h,550),((z+1)/h,75),(1,75)])+4*math.sin(m*1.7)
    stamp=lambda m:f'{2+int(m)//60:02d}:{int(m)%60:02d}'
    pts=[[round(i*h/180,4),round(fn(i*h/180),3)] for i in range(181)]
    ev=[('first',f,'첫 흔적','amber'),('alert',a,'알람 발화','red'),('response',r,'대응 시작','purple'),('recovery',z,'복구','green')]
    return dict(kind='trend',title='첫 흔적에서 복구까지의 시간을 나누기',claim='다음엔 더 빨리 알고 더 빨리 끝내려면, 두 간격을 줄인다.',
        source='설명용 합성 곡선. 사건 시각은 예시',data_kind='example',
        time=dict(unit='분',end=h,ticks=[[x,stamp(x)] for x in range(0,int(h)+1,30)]),
        panels=[dict(label='P99 응답 시간',unit='ms',max=700,ticks=[600,300,0],decimals=0,series=[dict(name='P99',color='blue',points=pts)])],
        thresholds=[dict(panel='P99 응답 시간',value=300,label='알람 임계선 300ms')],
        events=[dict(name=k,at=t,label=f'{stamp(t)} {lb}',color=c) for k,t,lb,c in ev],
        bands=[dict(**{'from':'first','to':'alert'},label='감지 공백 {duration}',color='amber')],
        captions=[dict(at=0,text='복구가 끝났다. 그래프를 되감아 사건을 다시 맞춘다.'),
                  dict(at='first',text=f'{stamp(f)} 첫 흔적. 아직 알람은 없다.'),
                  dict(at='alert',text=f'{stamp(a)} 알람. 첫 흔적에서 {fmt(a-f)}분이 지났다.'),
                  dict(at='response',text=f'{fmt(r-a)}분 뒤 대응 시작, 그로부터 {fmt(z-r)}분 뒤 복구.'),
                  dict(at=z+(h-z)*.4,text='다음엔 더 빨리 알고 더 빨리 끝내려면, 두 간격을 줄인다.')]),dict(intervals={'감지 공백':a-f,'알림 → 복구':z-a,'알림 → 대응 시작':r-a,'대응 시작 → 복구':z-r})

def postmortem_live_data(p):
    sp,extra=postmortem_spec(p);d,a,n,t,num_,info=_from_spec(sp,'',extra)
    iv=extra['intervals']
    aria=(f"P99 응답 시간과 네 사건. 첫 흔적에서 알람까지 {fmt(iv['감지 공백'])}분(감지 공백), 알람에서 대응 시작까지 {fmt(iv['알림 → 대응 시작'])}분, "
          f"대응 시작에서 복구까지 {fmt(iv['대응 시작 → 복구'])}분.")
    return d,aria,n,t,num_

def _pts(fn,end,n):return [[round(i*end/n,5),round(fn(i*end/n),3)] for i in range(n+1)]

def traffic_spec(p):
    """TrafficPattern: four 48-hour shapes in a 2 x 2 grid, each named by a pill."""
    base=lambda t:1800+6300*(max(0,math.sin(2*math.pi*(t*2-.22)))**2)+250*math.sin(t*math.pi*16)
    fs=[('① 평소 모양','ok',lambda t:base(t),[]),('② 수직 급락','bad',lambda t:base(t) if t<.7 else 180+80*math.sin(t*32),[(.7*48,'급락 발생','red')]),
        ('③ 수직 급증','warn',lambda t:base(t)*.45 if t<.55 else 8500+160*math.sin(t*24),[(.55*48,'급증 발생','amber')]),
        ('④ 새벽의 규칙적 스파이크','purple',lambda t:min(10000,base(t)+7000*sum(math.exp(-((t-u)/.009)**2) for u in [4/48,28/48])),[(4,'새벽 4시','purple'),(28,'다음 날 4시','purple')])]
    groups=[dict(pill=[[0,lb,tone]],panels=[dict(label=f'RPS {i+1}',hide_label=True,unit='',max=10000,ticks=[10000,5000,0],decimals=0,
                 series=[dict(name='RPS',color='blue',points=_pts(lambda h,f=fn:f(h/48),48,192))])],
                 events=[dict(name=f'e{i}{k}',at=a,label=l,color=c) for k,(a,l,c) in enumerate(ev)]) for i,(lb,tone,fn,ev) in enumerate(fs)]
    return dict(kind='trend',title='트래픽 모양으로 원인 후보를 좁힌다',claim='모양은 단서다. 같은 시간대의 반복부터 비교한다.',
        source='설명용 합성 RPS. 48시간',data_kind='example',time=dict(unit='시',end=48,ticks=[[0,'0시'],[24,'24시'],[48,'48시']]),groups=groups,
        captions=[dict(at=0,text='RPS(초당 요청 수)를 이틀치 겹쳐 본다. 평소에는 매일 같은 모양이다.'),
                  dict(at=26.4,text='급락은 유입 경로 장애, 급증은 이벤트나 봇을 먼저 의심한다.'),
                  dict(at=36,text='새벽 4시마다 튀는 스파이크는 배치나 크론을 의심한다.')]),{}

def survivorship_spec(p):
    """Survivorship: errors jump, the success-only P99 'improves' because fast failures leave the sample."""
    pre=stats([80,140],[900,99]);post=stats([75],[500]);E=60.0;t0=.4*E
    err=_pts(lambda t:piece(t/E,[(0,.1),(.4,.1),(.47,50),(1,50)]),E,120)
    lat=_pts(lambda t:piece(t/E,[(0,pre['p99']),(.4,pre['p99']),(.5,post['p99']),(1,post['p99'])])+3*math.sin(t*.7),E,120)
    return dict(kind='trend',title='에러가 늘자 P99가 좋아졌다?',claim='P99는 성공한 요청만 본다. 빠르게 실패한 요청은 통계에서 빠진다.',
        source='설명용 합성값. 성공 요청만 지연 분포에 집계하는 예',data_kind='example',time=dict(unit='초',end=E,ticks=[[0,'0'],[E,f'{E:g}초']]),
        panels=[dict(label='에러율',unit='%',max=50,ticks=[50,25,0],decimals=0,series=[dict(name='에러율',color='red',points=err)]),
                dict(label='P99 응답 시간',unit='ms',max=200,ticks=[200,100,0],decimals=0,series=[dict(name='P99',color='purple',points=lat)])],
        events=[dict(name='reject',at=t0,label='DB 커넥션 거부 시작',color='red')],
        stream=dict(after='에러율',label='요청',phases=[{'from':0,'divert':0.001,'color':'blue','divert_color':'red'},
                    {'from':'reject','divert':.5,'color':'blue','divert_color':'red','note':'3ms 실패 — 즉시 이탈'}],end_note='정상 처리 — 지연 분포에 남음'),
        annotations=[dict(at=E*.8,panel='P99 응답 시간',series='P99',text='좋아진 게 아니다',color='red',side='above')],
        captions=[dict(at=0,text='평소: 에러율 0.1%, P99는 140ms 근처.'),
                  dict(at='reject',text='DB가 커넥션을 거부한다. 요청 절반이 밀리초 만에 실패한다.'),
                  dict(at=E*.62,text='P99가 75ms로 \'개선\'됐다. 실패한 요청이 빠졌을 뿐이다.')]),dict(before=pre,after=post,
        populations={'before':{'success':999,'failure':1,'p99':pre['p99']},'after':{'success':500,'failure':500,'p99':post['p99']}},error_final=50,p99_success_final=post['p99'])

def memory_spec(p):
    """MemoryLeak: two sawtooths side by side; the floor after each GC tells them apart."""
    E=100.0
    normal=lambda t:35+38*((t/E*7)%1)
    def leak(t):
        u=t/E
        if u<.82:return min(100,30+int(u*7)*9+38*((u*7)%1))
        if u<.85:return 2
        return 13+25*((u-.85)/.15)
    fa=[[round(i*E/7,4),35] for i in range(1,7)];fb=[[round(i*E/7,4),30+i*9] for i in range(1,6)]
    g=lambda lb,col,fn,fl,fc,note,extra:dict(title=lb,color=col,events=extra or [],panels=[dict(label=lb,hide_label=True,unit='%',max=110,ticks=[100,50,0],decimals=0,
        series=[dict(name='힙',color='blue',points=_pts(fn,E,700)),dict(name='GC 후 최저점',color=fc,points=fl,style='dashed',dots=True,area=False,label=False)])])
    return dict(kind='trend',title='톱니보다 GC 뒤 바닥을 본다',claim='GC 직후 최저점이 계속 오르면 누수다.',source='설명용 합성 힙 사용률',data_kind='example',
        time=dict(unit='분',end=E,ticks=[[0,'시작'],[E,'끝']]),
        groups=[g('정상 (GC 톱니)','green',normal,fa,'green','',None),g('메모리 누수','red',leak,fb,'red','',[dict(name='oom',at=82,label='OOM',color='red'),dict(name='restart',at=85,label='재시작',color='purple')])],
        thresholds=[dict(panel='정상 (GC 톱니)',value=100,label='힙 한계'),dict(panel='메모리 누수',value=100,label='힙 한계')],
        annotations=[dict(at=round(3*E/7,4),panel='정상 (GC 톱니)',series='GC 후 최저점',text='GC 후 최저점: 수평 = 건강',color='green',side='below'),
                     dict(at=round(3*E/7,4),panel='메모리 누수',series='GC 후 최저점',text='최저점 계속 상승 = 누수',color='red',side='below')],
        captions=[dict(at=0,text='두 서버 모두 힙이 톱니 모양으로 오르내린다.'),
                  dict(at=round(3*E/7,4),text='봐야 할 것은 GC 직후의 최저점이다.'),
                  dict(at='oom@1',text='바닥이 계속 오른 쪽은 결국 힙 한계에 닿아 죽는다.')]),{}

def utilization_spec(p):
    """UtilizationCurve: queueing wait vs utilisation (M/M/1, normalised to 50%)."""
    E=95.0;w=lambda u:(u/100)/(1-u/100)
    pts=[[float(u),round(w(u),4)] for u in range(0,96)]
    return dict(kind='trend',title='사용률이 오르면 대기는 급격히 늘어난다',claim='100% 가동은 목표가 아니라 사고다. 80%부터 대기가 가파르다.',
        source='M/M/1 모델의 평균 대기, 사용률 50%를 1로 정규화',data_kind='estimate',time=dict(unit='%',end=E,ticks=[[0,'0%'],[50,'50%'],[70,'70%'],[80,'80%'],[90,'90%'],[95,'95%']]),
        panels=[dict(label='평균 대기 시간 (50% 대비)',unit='x',max=20,ticks=[15,10,5,1],decimals=1,series=[dict(name='대기',color='blue',points=pts,area=False)])],
        events=[dict(name='risk',at=80,label='위험선 80%',color='amber')],
        bands=[dict(**{'from':'risk','to':'end'},label='위험 구간',color='red')],
        annotations=[dict(at=90,panel='평균 대기 시간 (50% 대비)',series='대기',text=f'사용률 90% → 대기 {w(90):.0f}x',color='red',side='above')],
        captions=[dict(at=0,text='사용률이 오르면 대기는 비례가 아니라 곡선으로 늘어난다.'),
                  dict(at=70,text=f'70%에서 대기는 50%일 때의 {w(70):.1f}배다.'),
                  dict(at=88,text=f'90%면 {w(90):.0f}배, 95%면 {w(95):.0f}배. 100%는 목표가 아니라 사고다.')]),{'normalized_wait':[(r,(r)/(1-r)) for r in [.5,.7,.8,.9,.95]]}

def cache_spec(p):
    """CacheStampede: a hot key expires, misses go to the DB at once."""
    total=finite(p['requests_per_second'],'requests_per_second',1);normal=finite(p['normal_hit_percent'],'normal_hit_percent',0,100);low=finite(p['minimum_hit_percent'],'minimum_hit_percent',0,normal)
    E=60.0;hit=lambda t:piece(t/E,[(0,normal),(.4,normal),(.42,low),(.56,low),(.78,normal),(1,normal)])
    top=total*1.1
    return dict(kind='trend',title='인기 키가 만료되는 순간',claim='한 명만 다시 계산하게 하라 — 잠금, 조기 갱신, TTL 지터.',
        source=f'설명용 합성값. 총 {fmt(total)}건/s 일정, 미스당 DB 1회',data_kind='example',time=dict(unit='초',end=E,ticks=[[0,'0'],[E,f'{E:g}초']]),
        panels=[dict(label='캐시 히트율',unit='%',max=100,ticks=[100,50,0],decimals=0,series=[dict(name='히트율',color='green',points=_pts(hit,E,120))]),
                dict(label='DB QPS',unit='',max=round(top),ticks=[round(total),round(total/2),0],decimals=0,series=[dict(name='DB',color='purple',points=_pts(lambda t:total*(1-hit(t)/100),E,120))])],
        events=[dict(name='ttl',at=.4*E,label='인기 키 TTL 만료',color='amber'),dict(name='heal',at=.78*E,label='회복',color='green')],
        stream=dict(after='캐시 히트율',label='요청',box='캐시 HIT',side='DB',phases=[{'from':0,'divert':1-normal/100,'color':'blue','divert_color':'purple'},
                    {'from':'ttl','divert':1-low/100,'color':'blue','divert_color':'purple','note':'동시 미스 → DB 직행'},{'from':'heal','divert':1-normal/100,'color':'blue','divert_color':'purple'}],end_note='빠른 응답'),
        captions=[dict(at=0,text=f'평소: 히트율 {fmt(normal)}%. DB는 캐시 뒤에서 한가하다.'),
                  dict(at='ttl',text=f'인기 키가 만료되자 요청이 한꺼번에 DB로 간다. 히트율 {fmt(low)}%.'),
                  dict(at='heal',text='캐시가 다시 채워지면 DB는 조용해진다.')]),dict(total=total,normal=normal,low=low,
        hit=[[t,hit(t)] for t,_ in _pts(hit,E,120)],qps=[[t,total*(1-hit(t)/100)] for t,_ in _pts(hit,E,120)])

def deploy_spec(p):
    """Deploy: two scenarios after the same deploy; direction, not level, decides."""
    E=60.0
    first=lambda t:piece(t/E,[(0,80),(.25,80),(.31,220),(.62,95),(1,85)])+2*math.sin(50*t/E)
    second=lambda t:piece(t/E,[(0,80),(.25,80),(.31,245),(.75,310),(.84,85),(1,80)])+2*math.sin(50*t/E)
    g=lambda lb,col,fn,ev,note,nc,at:dict(title=lb,color='gray',events=ev,panels=[dict(label=lb,hide_label=True,unit='ms',max=360,ticks=[300,200,100],decimals=0,series=[dict(name='P99',color=col,points=_pts(fn,E,240))])])
    return dict(kind='trend',title='가장 위험한 30분',claim='B는 롤백 후 빠르게 회복한다. 판단 기준은 수치가 아니라 방향이다.',source='설명용 합성 P99',data_kind='example',
        time=dict(unit='분',end=E,ticks=[[0,'0'],[E,'시간 →']]),
        groups=[g('시나리오 A','blue',first,[dict(name='deployA',at=.25*E,label='배포',color='purple')],'',None,None),
                g('시나리오 B','blue',second,[dict(name='deployB',at=.25*E,label='배포',color='purple'),dict(name='rollback',at=.75*E,label='롤백',color='red')],'',None,None)],
        annotations=[dict(at=.5*E,panel='시나리오 A',series='P99',text='회복 추세 — 워밍업',color='green',side='above'),
                     dict(at=.7*E,panel='시나리오 B',series='P99',text='악화 추세',color='red',side='below')],
        captions=[dict(at=0,text='배포 전: 두 시나리오 모두 안정. 배포 마커는 반드시 남겨라.'),
                  dict(at=.3*E,text='배포 직후 둘 다 튄다. 아직 판단하지 않는다.'),
                  dict(at=.6*E,text='A는 내려오고, B는 계속 오른다. B는 롤백한다.'),
                  dict(at=.86*E,text='B는 롤백 후 빠르게 회복한다. 기준은 방향이다.')]),{}

def spike_spec(p):
    """MemorySpike: the heap steps up at one moment; the access log at that second names the request."""
    E=25.0;cut=15.0
    heap=lambda t:30+30*((t/E*6)%1) if t<cut else piece(t/E,[(.6,65),(.62,65),(.64,88),(1,93)])
    clock=lambda s_:f'14:{31+(50+int(s_))//60:02d}:{(50+int(s_))%60:02d}'
    lines=[[2,'14:31:52  GET /api/products 200 · 12ms'],[6,'14:31:56  GET /api/cart 200 · 9ms'],[10,'14:32:00  POST /api/orders 201 · 24ms'],
           [13,'14:32:03  GET /api/products 200 · 11ms'],[cut,'14:32:05  GET /api/orders/export?range=all 200 · 8,412ms','hot'],[20,'14:32:10  GET /api/cart 200 · 10ms']]
    return dict(kind='trend',title='메모리 스파이크의 범인 찾기',claim='같은 시각의 액세스 로그에서 범인 요청이 보인다.',source='설명용 합성 힙과 합성 로그',data_kind='example',
        time=dict(unit='초',end=E,ticks=[[0,clock(0)],[E,clock(E)]]),
        panels=[dict(label='힙 사용량',unit='%',max=110,ticks=[100,50,0],decimals=0,series=[dict(name='힙',color='blue',points=_pts(heap,E,250),area=False)])],
        thresholds=[dict(panel='힙 사용량',value=100,label='힙 한계')],events=[dict(name='spike',at=cut,label=clock(cut),color='red')],
        log=dict(label='액세스 로그',lines=lines),
        captions=[dict(at=0,text='평소의 톱니 — GC가 만드는 정상 리듬.'),dict(at='spike',text=f'{clock(cut)}, 힙이 계단처럼 뛰고 내려오지 않는다.'),
                  dict(at=cut+2.5,text='같은 시각의 액세스 로그에서 범인 요청이 보인다.')]),{}

def percentile_spec(p):
    """Percentile: two servers with the same mean; the tail decides."""
    a=stats(p['a_values'],p['a_counts']);b=stats(p['b_values'],p['b_counts'])
    return dict(kind='distribution',title='평균이 같은 두 서버',claim='평균은 같지만 P99는 6배 차이다. 평균은 꼬리를 숨긴다.',
        source='설명용 합성 요청 40건씩',data_kind='example',unit='ms',max=1000,
        groups=[dict(label='서버 A',values=p['a_values'],counts=p['a_counts']),dict(label='서버 B',values=p['b_values'],counts=p['b_counts'])],
        markers=['mean','p50','p95','p99'],tail={'from':400,'label':'긴 꼬리 (요청의 {share}%)'},
        captions=[dict(at=0,text='요청 40건씩, 점 하나가 요청 한 건이다.'),
                  dict(at='mean',text=f'평균 응답 시간은 둘 다 {fmt(a["mean"])}ms — 평균만 보면 똑같다.'),
                  dict(at='p95',text=f'P95부터 갈린다. B는 {fmt(b["p95"])}ms다.'),
                  dict(at='tail',text=f'평균은 같지만 P99는 {b["p99"]/a["p99"]:.1f}배 차이 ({fmt(a["p99"])}ms vs {fmt(b["p99"])}ms).')]),{'서버 A':a,'서버 B':b}

def r1(x):return math.floor(x*10+.5)/10   # half up, like the scenes' Math.round(x*10)/10

def _custom(scene,captions,end,base,**fields):
    """Data for a case-specific live scene: captions bound to model times, paced to be readable."""
    caps=sorted([[round(t,6),'',x] for t,x in captions],key=lambda c:c[0])
    for i,c in enumerate(caps):c[1]='①②③④⑤⑥⑦⑧'[i]
    return dict(scene=scene,captions=caps,rate=paced_rate(caps,end,base),**fields)

def throttle_model(p):
    period=finite(p['period_ms'],'period',1,1000);quota=finite(p['quota_ms'],'quota',1,period);low=finite(p['low_use_ms'],'low_use',.001,quota)
    n=p['periods'];change=p['load_start_period']
    if not isinstance(n,int) or not 3<=n<=10 or not isinstance(change,int) or not 1<=change<n:raise ValueError('Invalid period count/change')
    rows=[[i,low if i<change else quota,0 if i<change else period-quota] for i in range(n)]
    base=60.0;hi=base+(period-quota)*3.5   # waiting out the throttled part of each period lands in the tail latency
    p99=lambda t:base+(hi-base)*min(1,max(0,(t-change)/1.2))**2+5*math.sin(t*9)
    return dict(period=period,quota=quota,low=low,n=n,change=change,rows=rows,p99=p99,hi=hi)

def throttle_live_data(p):
    m=throttle_model(p);n=m['n'];ch=m['change']
    ts=[round(i*n/140,4) for i in range(141)]
    caps=[(0,f'부하가 낮을 땐 주기당 할당량({fmt(m["quota"])}ms) 안에서 끝난다.'),
          (ch,f'부하가 늘자 {fmt(m["quota"])}ms를 일찍 다 쓰고, 남은 {fmt(m["period"]-m["quota"])}ms는 강제로 멈춘다.'),
          (ch+1.6,'CPU 사용률 그래프는 평온한데 P99만 뛴다.')]
    d=_custom('cfs',caps,float(n),[[0,n/11]],period=m['period'],quota=m['quota'],rows=m['rows'],change=ch,
              series=dict(t=ts,v=[round(m['p99'](t),2) for t in ts]),ymax=300 if m['hi']<280 else nice_max(m['hi']*1.15))
    aria=(f"CFS 할당량 {fmt(m['quota'])}ms/{fmt(m['period'])}ms 컨테이너. 처음 {ch}주기는 {fmt(m['low'])}ms만 쓰고 끝나지만, 이후에는 {fmt(m['quota'])}ms를 다 쓰고 "
          f"{fmt(m['period']-m['quota'])}ms 동안 강제로 멈춰 P99가 약 {fmt(m['hi'])}ms로 오른다.")
    notes='설명용 합성 모델. CPU 사용률 지표는 실행한 시간만 세므로 스로틀된 시간은 보이지 않는다. P99는 강제 대기를 반영한 합성 곡선.'
    table=(['주기','실행 ms','스로틀 ms'],[[r[0]+1,r[1],r[2]] for r in m['rows']])
    return d,aria,notes,table,dict(quota=m['quota'],period=m['period'],rows=[[r[0]+1,r[1],r[2],m['period']-r[1]-r[2]] for r in m['rows']])

def timeout_model(p):
    gw=finite(p['gateway_timeout'],'gateway_timeout',.1,60);be=finite(p['backend_duration'],'backend_duration',gw+.01,90);h=finite(p['horizon'],'horizon',be,120)
    sample=[.6,.9,1.4,1.8,2.2,2.7,3.5,4.2,be,5.5 if be<5.5 else be+.5]   # ten requests; the animated one takes `be` seconds
    slow=sum(1 for x in sample if x>gw)
    return dict(gw=gw,be=be,h=h,sample=sample,gw_error=slow/len(sample)*100,be_success=100.0)

def timeout_live_data(p):
    m=timeout_model(p)
    caps=[(0,f'게이트웨이는 {fmt(m["gw"])}초까지만 기다린다. 백엔드의 쿼리는 {fmt(m["be"])}초짜리다.'),
          (m['gw'],f'{fmt(m["gw"])}초, 게이트웨이가 포기하고 사용자에게 504를 보낸다.'),
          (m['be'],'백엔드는 일을 끝내고 200을 기록한다. 받을 쪽은 이미 없다.'),
          (m['be']+.45*(m['h']-m['be']),'두 대시보드가 다른 말을 하면 타임아웃 계층부터 의심하라.')]
    d=_custom('timeout',caps,m['h'],[[0,.8]],gw=m['gw'],be=m['be'],end_h=m['h'],gw_error=m['gw_error'],be_success=m['be_success'])
    aria=(f"사용자, 게이트웨이(타임아웃 {fmt(m['gw'])}초), 백엔드(처리 {fmt(m['be'])}초). 게이트웨이는 {fmt(m['gw'])}초에 504를 돌려주고, 백엔드는 {fmt(m['be'])}초에 성공으로 끝난다. "
          f"그래서 게이트웨이 대시보드에는 504 에러율 {m['gw_error']:.0f}%, 백엔드에는 성공률 100%가 찍힌다.")
    notes=f"설명용 합성 모델. 요청 10건의 백엔드 처리 시간 {', '.join(fmt(x) for x in m['sample'])}초 중 {fmt(m['gw'])}초를 넘는 것이 게이트웨이에서 504가 된다."
    table=(['관찰자','결과','시점 s'],[['사용자/게이트웨이','504',m['gw']],['백엔드','200 (응답 미수신)',m['be']]])
    return d,aria,notes,table,dict(gateway_timeout=m['gw'],backend_duration=m['be'],unobserved_work=m['be']-m['gw'],request_count=1,gateway_error_percent=m['gw_error'])

def cascade_live_model():
    """Three servers behind a load balancer; the DB slows, requests hold threads longer, a saturated
    server fails its health check and its share moves to the others (dt = 0.01 s)."""
    base=[31.0,26.0,34.0];slow=2.0;H=15.0;dt=.01;grace=.8
    k=lambda t:1+2.0*min(1,max(0,(t-slow)/4.0))**1.4   # how much longer each request holds a worker
    alive=[True]*3;hit=[None]*3;fail=[None]*3;ts=[];loads=[];healthy=[]
    for i in range(int(H/dt)+1):
        t=round(i*dt,4);n=sum(alive)
        L=[min(100.0,base[j]*k(t)*3/n) if alive[j] else 0.0 for j in range(3)]
        for j in range(3):
            if alive[j] and L[j]>=100 and hit[j] is None:hit[j]=t
        # one health-check removal at a time: the first to saturate (then the more loaded) goes first
        cand=sorted([j for j in range(3) if alive[j] and hit[j] is not None],key=lambda j:(hit[j],-base[j]))
        last=max([x for x in fail if x is not None],default=-1e9)
        if cand and sum(alive)>1 and t>=max(hit[cand[0]],last)+grace:j=cand[0];alive[j]=False;fail[j]=t;L[j]=0.0
        ts.append(t);loads.append(L);healthy.append(sum(alive))
        if sum(alive)==1 and t>=max(x for x in fail if x is not None)+grace-.05:break   # end on the last server, saturated, just before its own removal
    H=ts[-1]
    return dict(base=base,slow=slow,H=H,ts=ts,loads=loads,healthy=healthy,hit=hit,fail=fail)

def cascade_live_data(p):
    m=cascade_live_model();f=sorted([(t,j) for j,t in enumerate(m['fail']) if t is not None])
    caps=[(0,'정상: 트래픽이 3대에 고르게 나뉜다.'),(m['slow'],'DB가 느려지자 요청이 서버에 오래 머문다.')]
    if f:caps.append((f[0][0],f'서버 {f[0][1]+1}이 헬스체크에 실패해 빠지고, 몫이 남은 서버로 간다.'))
    if len(f)>1:caps.append((f[1][0],'빠진 서버의 몫이 남은 서버를 더 빨리 쓰러뜨린다 — 도미노.'))
    step=10   # ship every 10th sample (0.1 s); the scene interpolates
    d=_custom('cascade',caps,m['H'],[[0,.9],[m['slow'],.6]],ts=m['ts'][::step],loads=[[round(x,2) for x in L] for L in m['loads'][::step]],
              hit=m['hit'],fail=m['fail'],slow=m['slow'],end_h=m['H'],healthy=m['healthy'][::step])
    order=', '.join(f'{fmt(t)}초에 서버 {j+1}' for t,j in f)
    aria=(f"로드 밸런서 뒤 서버 3대와 DB. {fmt(m['slow'])}초에 DB가 느려지자 서버 부하가 오르고, 포화된 서버가 헬스체크에서 빠진다({order}). "
          "빠진 서버의 몫이 남은 서버로 넘어가 연쇄적으로 무너진다.")
    notes='설명용 결정론적 모델. 부하 = 기본 부하 × 요청 점유 배수 × (3 / 정상 서버 수), 100%에 닿은 뒤 0.6초 안에 헬스체크로 제외된다.'
    table=(['서버','기본 부하 %','포화 시각 s','제외 시각 s'],[[f'서버 {j+1}',m['base'][j],m['hit'][j] if m['hit'][j] is not None else '-',m['fail'][j] if m['fail'][j] is not None else '-'] for j in range(3)])
    marks=[0.0,m['slow']]+sorted(t for t in m['fail'] if t is not None)+[m['H']]
    hs=[m['healthy'][min(len(m['ts'])-1,int(round(t/.01)))] for t in marks]
    return d,aria,notes,table,dict(failures=sorted(t for t in m['fail'] if t is not None),healthy=hs,shares_sum=[(t,h*(1/h)) for t,h in zip(marks,hs)],healthy_final=m['healthy'][-1])

def eventloop_live_data(p):
    from mechanism_scenes import event_model
    m=event_model(p);a,b,h=m['block_start'],m['block_end'],m['horizon']
    tasks=[[round(t['ready'],5),round(t['start'],5),round(t['end'],5),t['kind'],t['label']] for t in m['tasks'] if t['start']<=h+1e-9]
    io=[[round(x['start'],5),round(x['finish'],5),round(x['ready'],5)] for x in m['io']]
    caps=[(0,'요청은 큐에서 하나씩 루프로 들어가 금방 끝난다.'),(a,f'무거운 CPU 작업({fmt(b-a)}초)이 들어오면 루프가 그 자리에서 멈춘다.'),
          (a+.45*(b-a),'그동안 들어온 요청은 큐에 쌓이고, 루프 지연이 늘어난다.'),(b,'작업이 끝나야 밀린 큐가 한꺼번에 처리된다. 루프 지연이 곧 응답 지연이다.')]
    d=_custom('eventloop',caps,h,[[0,.5],[a,.45],[b,.5]],tasks=tasks,io=io,a=a,b=b,end_h=h,cpu_label='이미지 리사이즈')
    st=[x for x in m['states'] if x['t']<=h]
    aria=(f"Node.js 이벤트 루프. 평소엔 요청이 하나씩 금방 끝나지만, {fmt(a)}초에 {fmt(b-a)}초짜리 CPU 작업이 루프를 막아 그동안 큐가 최대 {max(x['queued'] for x in st)}건까지 쌓인다. "
          f"작업이 끝난 {fmt(b)}초 뒤에야 큐가 처리된다.")
    notes='설명용 결정론적 모델. 단일 스레드 루프가 큐의 작업을 순서대로 실행하고, I/O는 OS/libuv 스레드 풀에서 끝난 뒤 콜백으로 다시 큐에 들어온다.'
    table=(['작업','도착 s','시작 s','끝 s'],[[t[4],t[0],t[1],t[2]] for t in tasks])
    return d,aria,notes,table,dict(max_queue=max(x['queued'] for x in st),done=st[-1]['done'],block=[a,b])

def _loop_state(tasks,T):
    q=sum(1 for t in tasks if t[3]!='cpu' and t[0]<=T<t[1]);done=sum(1 for t in tasks if t[3] in ('normal','callback') and t[2]<=T)
    return q,done

def _spec_live(fn,aria):
    def build_(p):
        sp,extra=fn(p);d,a,n,t,num_,info=_from_spec(sp,'',extra);return d,aria,n,t,num_
    return build_

def _from_spec(spec,aria,extra=None):
    from visual_spec import build
    info=build(spec);numeric=dict(info['numeric']);numeric.update(extra or {})
    return info['data'],aria,info['notes'],info['table'],numeric,info

def pipeline_live_data(p):
    sp=pipeline_spec(p);h=p['horizon'];cap=p['application_capacity']
    d,a,n,t,num_,info=_from_spec(sp,'')
    q=num_['lanes'][0]['queue_end']
    aria=(f"Gateway, Application, DB 순서의 파이프라인. {p['change_time']:g}초에 유입이 {grp(p['before_rate'])}에서 {grp(p['after_rate'])}건/s로 늘자 한도 {grp(cap)}건/s인 "
          f"Application 앞에 매초 {grp(p['after_rate']-cap)}건씩 대기가 쌓여 {h:g}초에 {grp(q)}건이 된다. DB는 한도 {grp(p['database_capacity'])}건/s 중 {grp(cap)}건/s만 받는다.")
    return d,aria,n,t,num_

def bounded_live_data(p):
    sp=bounded_spec(p);d,a,n,t,num_,info=_from_spec(sp,'')
    u,b=num_['lanes']
    over=p['after_rate']*(p['horizon']-p['change_time'])
    num_.update(final_unbounded=u['queue_end'],final_bounded=b['queue_end'],rejected=b['rejected_end'],served=b['served_end'],
                overload_rejection_fraction=b['rejected_end']/over if over else 0)
    aria=(f"같은 유입과 처리 한도 {grp(p['capacity'])}건/s의 두 큐. {p['change_time']:g}초에 유입이 {grp(p['after_rate'])}건/s로 늘자 상한 없는 큐는 {p['horizon']:g}초에 "
          f"대기 {grp(u['queue_end'])}건까지 쌓이고, 상한 {p['queue_limit']:g}건 큐는 대기를 {p['queue_limit']:g}건으로 유지하며 {grp(b['rejected_end'])}건을 거부한다. "
          f"두 큐의 처리량은 {grp(b['served_end'])}건으로 같다.")
    return d,aria,n,t,num_

def cpu_live_data(p):
    sp,extra=cpu_spec(p);d,a,n,t,num_,info=_from_spec(sp,'',extra)
    aria=('세 서비스의 CPU 사용률과 P99 응답 시간을 같은 시간축에 위아래로 놓은 그림. 첫 번째는 둘 다 평온하다. 세 번째는 CPU가 100%로 오르며 '
          f"P99도 오른다(연산 포화 의심). 두 번째는 CPU가 {extra['b_cpu_mean']:.0f}% 근처인데 P99가 {sc_peak():g}ms로 오른다(대기 의심).")
    return d,aria,n,t,num_

def sc_peak():return cpu_scenarios()[1]['p99'](1)

def _probe_pool(p):
    jobs=pool_model(p)
    def probe(t):
        s=pool_state(jobs,t);return dict(state=dict(used=s['active'],queued=s['queued']),stats=[str(s['active']),str(s['queued'])])
    return probe

def live_checks(case_id,p):
    """Browser-gate inputs per live case: model expectation at T, sample times, and annotations
    that must be absent just before and present just after their event time."""
    if case_id=='cpu-throttling':
        m=throttle_model(p);d=throttle_live_data(p)[0];ts=d['series']['t'];vs=d['series']['v']
        return dict(expect=lambda T:dict(state={'p99':r1(interp(ts,vs,T)),'throttled':sum(1 for r in m['rows'] if r[2]>0 and T>=r[0]+m['quota']/m['period']-1e-9)},stats=[]),
                    samples=[.5,m['change']+.6,m['change']+1.5,m['n']-.5,m['n'],m['n']],annotations=[['컨테이너 스로틀 발생',m['change']+m['quota']/m['period']]],end=float(m['n']),resize_at=m['n']/2)
    if case_id=='timeout-mismatch':
        m=timeout_model(p)
        return dict(expect=lambda T:dict(state={'elapsed':r1(min(T,m['h'])),'gw504':int(T>=m['gw']-1e-9),'beDone':int(T>=m['be']-1e-9)},stats=[]),
                    samples=[.5,m['gw']-.2,m['gw']+.3,m['be']+.2,m['h'],m['h']],annotations=[['504 반환',m['gw']],['응답 버려짐',m['be']]],end=m['h'],resize_at=m['h']/2)
    if case_id=='cluster-cascade':
        m=cascade_live_model();ts=m['ts'];fl=sorted(t for t in m['fail'] if t is not None)
        def ex(T):
            i=min(len(ts)-1,int(round(T/.01)));return dict(state={'healthy':m['healthy'][i]},stats=[])
        sm=([.5,m['slow']+.8]+[t+.3 for t in fl][:3]+[m['H']-.4,m['H']])[:5]+[m['H']]
        return dict(expect=ex,samples=sm,annotations=[['재분배 중',fl[0]]] if fl else [],end=m['H'],resize_at=m['H']/2)
    if case_id=='event-loop':
        d=eventloop_live_data(p)[0];tk=d['tasks'];a_,b_,h=d['a'],d['b'],d['end_h']
        ex=lambda T:dict(state=dict(zip(('queued','done'),_loop_state(tk,T))),stats=[])
        return dict(expect=ex,samples=[.3*a_,a_+.2,(a_+b_)/2,b_+.05,b_+.4*(h-b_),h],annotations=[],end=h,resize_at=h/2)   # the CPU label leaves when the task ends
    if case_id=='thread-pool':
        data=pool_live_data(p)[0];ev=data['events'];jobs=pool_model(p);mj=jobs[ev['max_job']]
        samples=[.5,p['slow_start']+.6,(ev['t_queue'] or 5)+.5,ev['t_queue_max'] or 9,p['recovery']+1.5,p['horizon']]
        notes=[]   # the scene has no verdict labels any more; queue and response times are live state
        return dict(expect=_probe_pool(p),samples=samples,annotations=notes,end=p['horizon'],resize_at=6.0)
    spec={'pipeline-bottleneck':pipeline_spec,'bounded-queue':bounded_spec,'cpu-latency':lambda q:cpu_spec(q)[0],
          'slow-degradation':lambda q:slow_spec(q)[0],'postmortem-timeline':lambda q:postmortem_spec(q)[0],
          **{k:(lambda f:lambda q:f(q)[0])(f) for k,(f,_) in SPEC_CASES.items()}}[case_id](p)
    from visual_spec import build
    return build(spec)['checks']

LIVE_BUILDERS={'thread-pool':pool_live_data,'pipeline-bottleneck':pipeline_live_data,'bounded-queue':bounded_live_data,'cpu-latency':cpu_live_data,
               'slow-degradation':slow_live_data,'postmortem-timeline':postmortem_live_data}
SPEC_CASES={'traffic-patterns':(traffic_spec,'48시간 RPS의 네 가지 모양: 평소 반복, 수직 급락, 수직 급증, 새벽 4시의 규칙적 스파이크.'),
            'survivorship-bias':(survivorship_spec,'에러율이 50%로 뛰자 성공 요청만 집계한 P99가 오히려 내려간다. 빠르게 실패한 요청이 통계에서 빠졌기 때문이다.'),
            'memory-leak':(memory_spec,'정상 서버와 누수 서버의 힙. 정상은 GC 후 최저점이 수평이고, 누수는 최저점이 계속 올라 힙 한계에서 OOM이 난다.'),
            'utilization-wait':(utilization_spec,'M/M/1 모델에서 사용률에 따른 평균 대기(50%를 1로). 80%부터 가파르게 오른다.'),
            'cache-stampede':(cache_spec,'인기 키 TTL 만료 순간 캐시 히트율이 떨어지고, 미스가 한꺼번에 DB로 가 DB QPS가 치솟는다.'),
            'percentile-comparison':(percentile_spec,'평균 응답 시간이 같은 두 서버의 요청 분포. A는 100ms 근처에 모여 있고, B는 대부분 빠르지만 일부가 400ms 이상에 몰려 P99가 6배 높다.'),
            'memory-spike':(spike_spec,'힙 사용량과 같은 시각의 액세스 로그. 14:32:05에 힙이 계단처럼 뛰고, 그 시각의 로그에 8초 넘게 걸린 전체 내보내기 요청이 있다.'),
            'deploy-comparison':(deploy_spec,'같은 배포 뒤 두 시나리오. A는 워밍업 후 회복하고, B는 계속 악화되어 롤백 후 회복한다.')}
LIVE_BUILDERS.update({k:_spec_live(f,a) for k,(f,a) in SPEC_CASES.items()})
LIVE_BUILDERS['cpu-throttling']=throttle_live_data
LIVE_BUILDERS['timeout-mismatch']=timeout_live_data
LIVE_BUILDERS['cluster-cascade']=cascade_live_data
LIVE_BUILDERS['event-loop']=eventloop_live_data

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
