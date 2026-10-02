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

def cpu(s,p):
    scenarios=[('정상',lambda t:50+12*math.sin(t*9),lambda t:65+9*math.sin(t*9),G),('낮은 CPU · 높은 지연',lambda t:25+3*math.sin(t*17),lambda t:piece(t,[(0,75),(.35,75),(.6,900),(1,900)]),A),('CPU 포화',lambda t:piece(t,[(0,45),(.2,45),(.4,100),(1,100)]),lambda t:piece(t,[(0,70),(.2,70),(.4,920),(1,940)]),R)]
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
    fail=[.4,.6,.77]
    normal=s.track([(0,'opacity:1'),(.22,'opacity:1'),(.24,'opacity:0'),(1,'opacity:0')]);slow=s.reveal(.22)
    body=s.box(4,100,94,70,'LB','재분배')+s.box(405,100,90,70,'DB','정상',B,normal)+s.box(405,100,90,70,'DB','지연',R,slow)
    for i,at in enumerate(fail):
        y=25+i*94
        faded=s.track([(0,'opacity:1'),(at-.01,'opacity:1'),(at,'opacity:.22'),(1,'opacity:.22')])
        body+=f'<path class="mr-rail {faded}" d="M98 135 L185 {y+28} M315 {y+28} L405 135"/>'
        cls=s.track([(0,'opacity:1'),(at-.01,'opacity:1'),(at,'opacity:.38'),(1,'opacity:.38')])
        body+=s.box(185,y,130,56,f'서버 {i+1}',state=cls)
        cross=s.reveal(at)
        body+=f'<g class="{cross}"><path d="M275 {y+8} l23 23 m0 -23 l-23 23" stroke="{R}" stroke-width="3"/><text x="250" y="{y+78}" text-anchor="middle" style="fill:{R}">제외</text></g>'
        body+=s.token_stream(100,135,185,y+28,0,at,6)
    curves=[]
    for i,at in enumerate(fail):
        fn=lambda t,i=i,at=at:0 if t>=at else 100/sum(t<f for f in fail)
        curves.append((f'서버 {i+1}',samples(fn,101),[B,P,G][i]))
    shares=[[t,sum(0 if t>=at else 1/sum(t<f for f in fail) for at in fail)] for t in [0,.5,.7,.9]]
    s.numeric['shares_sum']=shares
    content=s.stack(s.panel('로드밸런서 → 3개 서버 → 공유 DB',s.svg(body,'서버 제외와 경로 재분배',325),'그림은 원인을 이미 지정한 합성 시나리오'),s.chart('남은 서버의 트래픽 분담',curves,'%',100,[(.4,'첫 제외',R),(.77,'대상 없음',R)]))
    return content,phase((0,'3개 대상으로 분배','각 서버는 정확히 1/3의 몫을 받는다.'),(.4,'한 대 제외','두 서버로 1/2씩 재분배된다.'),(.6,'남은 한 대','모든 새 요청이 마지막 한 곳으로 향한다.'),(.8,'보낼 대상 없음','공유 의존성의 회복 여부를 따로 확인해야 한다.'))

def event_loop(s,p):
    h=finite(p['horizon'],'horizon',1,60);a=finite(p['block_start'],'block_start',0,h);b=finite(p['block_end'],'block_end',a+.01,h)
    aa=a/h;bb=b/h
    theta=lambda t:540*t/aa if t<aa else 540 if t<bb else 540+720*(t-bb)/(1-bb)
    rotate=s.track([(i/80,f'transform:rotate({theta(i/80):.3f}deg);transform-origin:250px 125px') for i in range(81)])
    blocked=s.pulse(aa,bb)
    body='<path class="mr-rail" d="M70 125 H185 M315 125 H430 M250 190 V242"/><circle cx="250" cy="125" r="67" fill="#eef5ff" stroke="#759bcb" stroke-width="3"/>'
    body+=f'<g class="{rotate}"><circle cx="317" cy="125" r="8" fill="{B}"/></g><g class="{blocked}"><rect x="184" y="91" width="132" height="66" rx="8" fill="#fff0e4" stroke="{R}"/><text class="mr-label" x="250" y="118" text-anchor="middle">CPU 점유</text><text x="250" y="144" text-anchor="middle">{fmt(b-a)}초 정지</text></g>'
    body+=s.box(3,99,92,54,'대기')+s.box(405,99,92,54,'응답')+s.box(165,237,170,48,'위임 I/O')
    # Packets on I/O continue while the JS loop marker pauses; callbacks wait for the loop.
    body+=s.token_stream(250,198,250,235,0,.9,7,A)
    body+=s.token_stream(95,125,180,125,0,aa,5,B)+s.token_stream(320,125,405,125,bb,1,9,B)
    for i in range(6):
        at=aa+.015+i*(bb-aa-.07)/6;finish=min(.96,bb+.035+i*.035)
        cls=s.pulse(at,finish)
        body+=f'<circle class="{cls}" cx="{23+(i%3)*22}" cy="{181+(i//3)*23}" r="6" fill="{A}"/>'
    lag=samples(lambda t:0 if t<aa else (t-aa)*h*1000 if t<bb else (b-a)*1000*max(0,1-(t-bb)/.12))
    s.numeric.update(block_ms=(b-a)*1000,block_window=[aa,bb])
    return s.stack(s.panel('한 JS 실행 스레드',s.svg(body,'회전하는 이벤트 루프가 CPU 작업 구간에서 멈추고 다시 진행',302),'I/O 위임과 콜백 실행은 다른 단계'),s.chart('현재 콜백 대기 지연',[('예시 지연',lag,R)],'ms',(b-a)*1000*1.2,[(aa,'정지',R),(bb,'재개',G)])),phase((0,'위임과 실행','I/O를 기다리는 동안에도 루프는 다른 작업을 진행할 수 있다.'),(aa,'CPU 실행이 길어진다','위임된 외부 작업이 끝나도 루프의 콜백 처리는 기다린다.'),(bb,'루프 재개','대기 콜백을 처리하며 지연이 줄어든다.'))

def pipeline_flow(s,rows,p):
    horizon=p['horizon'];change=p['change_time']/horizon
    body='<path class="mr-rail" d="M8 85 H491"/>'
    body+=s.box(22,58,112,56,'Gateway')+s.box(230,58,124,56,'Application',color=R)+s.box(408,58,80,56,'DB')
    body+=s.token_stream(4,85,22,85,0,1,15)+s.token_stream(136,85,226,85,0,change,4)
    body+=s.token_stream(356,85,406,85,0,1,9)
    maxq=max(row['q'] for row in rows)
    for i in range(12):
        at=next((r['t']/horizon for r in rows if r['q']>=maxq*(i+1)/12),1)
        cls=s.reveal(max(0,at-.04))
        body+=f'<rect class="{cls}" x="{152+(i%6)*11}" y="{53+(i//6)*17}" width="8" height="11" rx="2" fill="{A}"/>'
    for x,label,cap,ratef in [(27,'GW',p['gateway_capacity'],lambda r:r['rate']),(236,'APP',p['application_capacity'],lambda r:r['served_rate']),(408,'DB',p['database_capacity'],lambda r:r['served_rate'])]:
        w=100 if x<400 else 78
        seq=[(r['t']/horizon,'transform:scaleX('+str(min(1,ratef(r)/cap))+');transform-origin:'+str(x)+'px 160px') for r in rows]
        cls=s.track(seq)
        body+=f'<rect x="{x}" y="155" width="{w}" height="8" fill="#e6edf5"/><rect class="{cls}" x="{x}" y="155" width="{w}" height="8" fill="{R if label=="APP" else G}"/><text x="{x+w/2}" y="186" text-anchor="middle">{fmt(cap)}/s</text>'
    body+=f'<text x="190" y="30" text-anchor="middle">대기 공간</text><text x="250" y="223" text-anchor="middle">점·작은 블록은 개수 비례가 아닌 경로/누적의 상징</text>'
    return s.panel('각 단계의 한도와 앞쪽 대기',s.svg(body,'세 단계 처리 한도와 Application 앞에 쌓이는 대기',237),'아래 게이지 = 처리율 / 단계별 한도')

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

BUILDERS={'traffic-patterns':traffic,'percentile-comparison':distributions,'survivorship-bias':survivorship,'cpu-latency':cpu,'cpu-throttling':throttling,'memory-leak':memory,'memory-spike':spike,'thread-pool':pool,'cluster-cascade':cascade,'event-loop':event_loop,'pipeline-bottleneck':pipeline,'utilization-wait':utilization,'bounded-queue':bounded,'cache-stampede':cache,'timeout-mismatch':timeout,'slow-degradation':slow,'deploy-comparison':deploy,'postmortem-timeline':postmortem,'gc-pause':gc_pause}

def build_case(meta,prefix=None):
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
    s=ReferenceScene(prefix);content,phases=BUILDERS[meta['id']](s,meta['params'])
    fragment=assemble(s,meta,content,phases)
    return fragment,s.numeric
