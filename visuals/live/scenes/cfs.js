/* Scene: CFS CPU quota throttling. Each 100 ms period is a cell: the blue part ran, the hatched
   part was forced to stop after the quota ran out; below, P99 latency on the same clock.
   Periods, quota and the P99 curve come from the Python model (monitoring_cases.throttle_model). */
CA_SCENES['cfs']=function(D,K,GR){
  var C=K.C,TP=GR.timePanels,R=D.rows,n=R.length,end=n,q=D.quota/D.period,S=D.series;
  function geom(W){var g={W:W,nw:W<560},x0=g.nw?30:34;g.x0=x0;g.x1=W-2;g.X=function(t){return g.x0+(g.x1-g.x0)*t/end;};
    g.sy=g.nw?52:50;g.sh=g.nw?34:44;g.p=TP.panelIn(x0,W-2,g.sy+g.sh+(g.nw?62:56),g.nw?96:120,end,D.ymax);
    g.pill=g.p.y+g.p.h+(g.nw?40:34);g.H=g.pill+(g.nw?40:16);return g;}
  function hatch(x0,x1,y,h){var o=K.rect(x0,y,x1-x0,h,{r:0,fill:C.redSoft});for(var k=-h;k<x1-x0;k+=7){var a=Math.max(x0,x0+k),b=Math.min(x1,x0+k+h);
      if(b>a)o+=K.line(a,y+h-(a-(x0+k)),b,y+h-(b-(x0+k)),C.red,{sw:1.1,op:.75});}return o;}
  function throttled(T){return R.filter(function(r){return r[2]>0&&T>=r[0]+q-1e-9;}).length;}
  function draw(T,g){var o='',y=g.sy,h=g.sh;
    o+=K.text(0,16,'CFS 주기 확대 ('+K.grp(D.period)+'ms 단위)',{fs:14,c:C.ink,w:700})+K.text(g.W,16,'quota '+K.grp(D.quota)+'ms/주기',{fs:12,c:C.muted,a:'end'});
    o+=K.rect(0,25,11,11,{r:2,fill:C.blue})+K.text(15,35,'실행',{fs:12,c:C.muted})+hatch(52,63,25,11)+K.text(67,35,'스로틀(강제 정지)',{fs:12,c:C.muted});
    R.forEach(function(r){var a=g.X(r[0])+3,b=g.X(r[0]+1)-3,w=b-a,qx=a+w*q;
      o+=K.rect(a,y,w,h,{r:3,fill:C.paper2,st:C.rule});
      var run=K.clamp((T-r[0])/(r[1]/D.period));if(T>r[0])o+=K.rect(a,y,w*r[1]/D.period*run,h,{r:0,fill:C.blue});
      if(r[2]>0&&T>=r[0]+q)o+=hatch(qx,qx+(w-(qx-a))*K.clamp((T-r[0]-q)/(1-q)),y,h);
      o+=K.line(qx,y,qx,y+h,C.faint,{d:'3 3'});});
    var lowEnd=g.X(D.change);o+=K.text(lowEnd/2+g.x0/2,y+h+17,'부하 낮음 · '+K.grp(R[0][1])+'ms만 사용',{fs:12,c:C.muted,a:'middle'});
    if(T>=D.change)o+=K.text((lowEnd+g.x1)/2,y+h+17,'부하 증가 · '+K.grp(D.quota)+'ms 조기 소진',{fs:12,c:C.muted,a:'middle'});
    if(T>=D.change+q){var first=g.X(D.change)+3+(g.X(D.change+1)-g.X(D.change)-6)*q;o+=K.text(first,y-6,K.grp(D.period-D.quota)+'ms 강제 대기',{fs:12,c:C.redText,a:'start',w:700,halo:1});}
    var p=g.p;o+=K.rect(p.x0,p.y,p.x1-p.x0,p.h,{r:3,fill:C.paper2,st:C.rule})+K.text(p.x0,p.y-8,'P99 응답 시간',{fs:13,c:C.text,w:700})+K.text(p.x1,p.y-8,'(ms)',{fs:11,c:C.muted,a:'end'});
    var lastY=-1e9;[D.ymax,D.ymax*2/3,D.ymax/3,0].forEach(function(v){var yy=p.Y(v);o+=K.line(p.x0,yy,p.x1,yy,C.rule);if(yy-lastY>=14){o+=K.text(p.x0-5,yy+4,K.grp(v),{fs:11,c:C.muted,a:'end'});lastY=yy;}});
    var pts=TP.cut(K,p,S.t,S.v,T);if(pts.length>1){var v=TP.at(S.t,S.v,T),x=p.X(Math.min(T,end)),yv=p.Y(v);
      o+=K.path('M'+K.f(p.X(0))+' '+K.f(p.Y(0))+'L'+pts.join('L')+'L'+K.f(x)+' '+K.f(p.Y(0))+'Z',C.purpleSoft,'1');
      o+='<path d="M'+pts.join('L')+'" fill="none" stroke="'+C.purple+'" stroke-width="2" stroke-linejoin="round"/>'+K.ring(x,yv,3.5,'#fff',C.purple,2);
      var right=x>p.x1-60;o+=K.text(right?x-7:x+7,Math.max(p.y+14,yv-8),K.grp(Math.round(v))+'ms',{fs:13,c:C.purpleText,a:right?'end':'start',w:700,halo:1});}
    if(T<end-1e-6)o+=K.line(g.X(T),y-2,g.X(T),p.y+p.h,C.faint,{d:'2 3'});
    o+=K.pill(p.x0,g.pill,'CPU 사용률 그래프: 이상 없음','ok',{a:'start',fs:12});
    if(T>=D.change+q){var pw=K.tw('CPU 사용률 그래프: 이상 없음',12)+14;o+=g.nw?K.pill(p.x0,g.pill+28,'컨테이너 스로틀 발생 ↑','bad',{a:'start',fs:12}):K.pill(p.x0+pw+10,g.pill,'컨테이너 스로틀 발생 ↑','bad',{a:'start',fs:12});}
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {p99:Math.round(TP.at(S.t,S.v,T)*10)/10,throttled:throttled(T)};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
