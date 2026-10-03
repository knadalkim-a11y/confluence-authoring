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
  /* One mechanism, as in the article demo: inflow, queue, the pool, the slow dependency.
     Response times are in the status line and the data table, not in a second chart. */
  function geom(W){var g=FQ.geom(W,30);g.H=g.bottom+12;return g;}
  function draw(T,g){var st=state(T),i,slow=T>=P.slow_start&&T<P.recovery;
    var cells=[],flash=[];for(i=0;i<P.workers;i++){var r=st.act[i];cells.push(r?{hot:false,progress:K.clamp((T-r.s)/r.svc),appear:K.clamp((T-r.s)/0.12)}:null);
      flash.push(0);J.forEach(function(x){if(x.slot===i&&T>=x.e&&T<x.e+0.2&&!r)flash[i]=Math.max(flash[i],1-(T-x.e)/0.2);});}
    var queue=st.qd.map(function(r){var pos=0;J.forEach(function(p){if(p.a<r.a-1e-9)pos+=T<p.s?1:K.clamp((p.s+SHIFT-T)/SHIFT);});return pos;});
    var transit=[];J.forEach(function(r){if(T>=r.a-TR&&T<r.a)transit.push({p:(T-(r.a-TR))/TR,target:r.s>r.a+1e-9?r.ahead:null});});
    return FQ.draw(K,g,{T:T,inflowLabel:D.labels.inflow,poolLabel:D.labels.pool,used:st.n,slots:P.workers,cells:cells,flash:flash,queue:queue,
      queueCount:st.qd.length,queueLabel:'대기 '+st.qd.length+'건',transit:transit,depLabel:D.labels.dependency,depValue:K.num(svcAt(T))+'초',depSlow:slow});}
  function stats(T){var st=state(T);
    return {left:[['사용 중 스레드 ',st.n,'/'+P.workers,st.n===P.workers],['대기 ',st.qd.length,'건',st.qd.length>0],
      ['체감 응답 ',st.last?K.num(st.last.e-st.last.a,2):'-',st.last?'초':'',st.last&&st.last.e-st.last.a>=D.axes.hot_response]]};}
  function probe(T){var st=state(T);return {used:st.n,queued:st.qd.length};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,probe:probe};
};
