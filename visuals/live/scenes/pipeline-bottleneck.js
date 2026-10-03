/* Scene: bottleneck in a pipeline. Queue, cumulative counts and token times come from the
   Python fluid model (data.series, data.tokens); this file only maps state at T. */
CA_SCENES['pipeline-bottleneck']=function(D,K,GR){
  var P=D.params,S=D.series,E=D.events,L=D.labels,C=K.C,FQ=GR.flowQueue,TP=GR.timePanels,cap=P.application_capacity;
  function q(T){return Math.max(0,TP.at(S.t,S.q,T));}
  function rateIn(T){return T<P.change_time-1e-9?P.before_rate:P.after_rate;}
  function served(T){var i=1;while(i<S.t.length-1&&S.t[i]<=T+1e-9)i++;return (S.srv[i]-S.srv[i-1])/(S.t[i]-S.t[i-1]);}
  function geom(W){var g=FQ.laneGeom(W,22,{source:true,dep:true,below:true}),nw=g.nw;
    g.A=TP.panelIn(nw?34:42,W-4,g.bottom+46,nw?80:92,P.horizon,D.axes.q_max);g.H=g.A.y+g.A.h+22;return g;}
  function draw(T,g){var o='',A=g.A,nw=g.nw,qv=q(T),sr=served(T),rin=rateIn(T),hot=qv>1e-6;
    o+=K.text(0,10,L.unit,{fs:11,c:C.faint});
    o+=FQ.laneDraw(K,g,{T:T,q:qv,qScale:D.axes.q_max,limit:null,qLabel:'대기 '+K.grp(qv)+'건',
      srcName:L.source,srcValue:(nw?'':'한도 ')+K.grp(P.gateway_capacity),srcFrac:rin/P.gateway_capacity,
      srvName:nw?L.server_short:L.server,srvValue:'한도 '+K.grp(cap),srvFrac:sr/cap,srvHot:hot,srvNote:hot?'한도 도달':'여유 '+K.grp(cap-sr),
      depName:L.dependency,depValue:'한도 '+K.grp(P.database_capacity),depFrac:sr/P.database_capacity,depNote:'여유 '+K.grp(P.database_capacity-sr),
      tokens:D.tokens,tail:q,TR:0.45,tokenRate:Math.max(P.before_rate,P.after_rate)/D.unit});
    o+=TP.title(K,A,L.panel)+TP.yTicks(K,A,[[0,'0'],[D.axes.q_max/2,K.grp(D.axes.q_max/2)],[D.axes.q_max,K.grp(D.axes.q_max)]],true);
    o+=TP.area(K,A,S.t,S.q,T,C.amber);
    if(T>=P.change_time)o+=TP.mark(K,A,A,P.change_time,L.change);
    o+=TP.xAxis(K,A,D.axes.x_step,'초')+TP.cursor(K,A,A,T);
    return o;}
  function stats(T){var qv=q(T),sr=served(T),rin=rateIn(T),d=rin-sr;
    return {left:[['새 요청 대기 ',K.num(qv/cap),'초',qv>1e-6]],
      right:['유입 − 처리 = ',K.grp(rin)+' − '+K.grp(sr),' = ',d>1e-6?K.grp(d)+'건/s씩 쌓임':'0건/s',d>1e-6]};}
  function probe(T){return {queue:Math.round(q(T)*10)/10};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,probe:probe};
};
