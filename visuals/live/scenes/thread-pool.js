/* Scene: worker pool exhaustion. All numbers come from the Python FIFO model (data.jobs,
   data.series, data.events); this file only maps model state at time T to the grammars. */
CA_SCENES['thread-pool']=function(D,K,GR){
  var P=D.params,E=D.events,S=D.series,C=K.C,TR=0.45,SHIFT=0.08,FQ=GR.flowQueue,TP=GR.timePanels;
  var J=D.jobs.map(function(j,i){return {i:i,a:j[0],s:j[1],e:j[2],slot:j[3],svc:j[4],hot:j[4]>P.normal_service+1e-9};});
  J.forEach(function(r){r.ahead=J.filter(function(x){return x.a<r.a-1e-9&&x.s>r.a+1e-9;}).length;});
  var maxJ=J[E.max_job],rate=1/P.arrival_interval;
  function svcAt(t){return t>=P.slow_start&&t<P.recovery?P.slow_service:P.normal_service;}
  function state(T){var act=[],qd=[],n=0;J.forEach(function(r){if(r.s<=T&&T<r.e){act[r.slot]=r;n++;}else if(r.a<=T&&T<r.s)qd.push(r);});
    var last=null;J.forEach(function(r){if(r.e<=T&&(!last||r.e>=last.e))last=r;});return {act:act,qd:qd,n:n,last:last};}
  function geom(W){var g=FQ.geom(W,24),nw=g.nw;g.A=TP.panel(g,g.bottom+40,nw?64:74,P.horizon,D.axes.stack_max);
    g.B=TP.panel(g,g.A.y+g.A.h+34,nw?64:74,P.horizon,D.axes.response_max);g.H=g.B.y+g.B.h+22;return g;}
  function draw(T,g){var st=state(T),o='',i,A=g.A,B=g.B,slow=T>=P.slow_start&&T<P.recovery;
    var cells=[],flash=[];for(i=0;i<P.workers;i++){var r=st.act[i];cells.push(r?{hot:r.hot,progress:K.clamp((T-r.s)/r.svc),appear:K.clamp((T-r.s)/0.12)}:null);
      flash.push(0);J.forEach(function(x){if(x.slot===i&&T>=x.e&&T<x.e+0.2&&!r)flash[i]=Math.max(flash[i],1-(T-x.e)/0.2);});}
    var queue=st.qd.map(function(r){var pos=0;J.forEach(function(p){if(p.a<r.a-1e-9)pos+=T<p.s?1:K.clamp((p.s+SHIFT-T)/SHIFT);});return pos;});
    var transit=[];J.forEach(function(r){if(T>=r.a-TR&&T<r.a)transit.push({p:(T-(r.a-TR))/TR,target:r.s>r.a+1e-9?r.ahead:null});});
    o+=FQ.draw(K,g,{T:T,inflowLabel:D.labels.inflow,poolLabel:D.labels.pool,used:st.n,slots:P.workers,cells:cells,flash:flash,queue:queue,
      queueCount:st.qd.length,queueLabel:'대기 '+st.qd.length+'건',transit:transit,depLabel:D.labels.dependency,depValue:K.num(svcAt(T))+'초',depSlow:slow});
    o+=TP.band(K,A,B,P.slow_start,P.recovery,D.labels.slow_band);
    o+=TP.title(K,A,'스레드 사용과 대기',[['사용 중',C.blue],['대기',C.amber]])+TP.yTicks(K,A,[[0,'0'],[P.workers,String(P.workers),C.red],[D.axes.stack_max,String(D.axes.stack_max)]]);
    var n=Math.min(S.active.length-1,Math.floor(T/S.dt+1e-6));
    o+=TP.stacked(K,A,S.dt,n,S.active,S.queued_smooth,C.blue,C.amber)+TP.limit(K,A,P.workers,'풀 한도 '+P.workers);
    if(E.q_max>0&&T>=E.t_queue_max)o+=K.text(A.X(E.t_queue_max),A.Y(P.workers+E.q_max)-6,'최대 대기 '+E.q_max+'건',{fs:11,c:C.amber,a:'middle',w:700});
    o+=TP.title(K,B,'요청별 체감 응답 시간')+TP.yTicks(K,B,D.axes.response_ticks.map(function(t){return [t,t?t+'초':'0'];}),true);
    J.forEach(function(r){if(r.e<=T){var hot=r.e-r.a>=D.axes.hot_response;o+=K.dot(B.X(r.e),B.Y(r.e-r.a),hot?3:2.6,hot?C.red:C.blue,hot?.9:.75);}});
    if(T>=J[0].e)o+=K.text(B.X(J[0].a),B.Y(P.normal_service)-8,'평소 '+K.num(P.normal_service)+'초',{fs:11,c:C.blue});
    if(maxJ&&T>=maxJ.e){var wait=maxJ.s-maxJ.a,resp=maxJ.e-maxJ.a;
      o+=K.text(B.X(maxJ.e)-9,B.Y(resp)+4,g.nw||wait<1e-9?'최대 '+K.num(resp)+'초':'최대 '+K.num(resp)+'초 = 대기 '+K.num(wait)+' + 처리 '+K.num(maxJ.svc),{fs:11,c:C.red,a:'end',w:700});}
    o+=TP.xAxis(K,B,D.axes.x_step,'초')+TP.cursor(K,A,B,T);
    return o;}
  function stats(T){var st=state(T),sv=svcAt(T),need=rate*sv,over=need>P.workers+1e-9;
    return {left:[['사용 중 스레드 ',st.n,'/'+P.workers,st.n===P.workers],['대기 ',st.qd.length,'건',st.qd.length>0],
      ['체감 응답 ',st.last?K.num(st.last.e-st.last.a,2):'-',st.last?'초':'',st.last&&st.last.e-st.last.a>=D.axes.hot_response]],
      right:['필요한 동시 처리 '+K.num(rate)+'건/s × ',K.num(sv)+'초',' = ',K.num(need)+'칸'+(over?' > '+P.workers:''),over]};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,state:state};
};
