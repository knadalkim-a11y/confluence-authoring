/* Scene: bottleneck in a pipeline. Queue, cumulative counts and token times come from the
   Python fluid model (data.series, data.tokens); this file only maps state at T. */
CA_SCENES['pipeline-bottleneck']=function(D,K,GR){
  var P=D.params,S=D.series,L=D.labels,C=K.C,FQ=GR.flowQueue,TP=GR.timePanels,cap=P.application_capacity;
  function q(T){return Math.max(0,TP.at(S.t,S.q,T));}
  function rateIn(T){return T<P.change_time-1e-9?P.before_rate:P.after_rate;}
  function served(T){var i=1;while(i<S.t.length-1&&S.t[i]<=T+1e-9)i++;return (S.srv[i]-S.srv[i-1])/(S.t[i]-S.t[i-1]);}
  function geom(W){var g=FQ.chainGeom(W,0,{stages:[0,1,2],queueAt:1,lead:true,tail:true,rows:2});g.H=g.bottom+18;return g;}
  function draw(T,g){var qv=q(T),sr=served(T),rin=rateIn(T),hot=qv>1e-6,unit=g.c?'':'건/s',lim=function(v){return (g.c?'':'한도 ')+K.grp(v)+unit;};
    var spare=hot?['여유(한가함)','ok']:null,o='';
    o+=FQ.chainDraw(K,g,{T:T,q:qv,unit:D.unit,tokens:D.tokens,tail:q,v:D.speed,qLabel:K.grp(qv)+'건 대기',qHot:true,qDot:C.red,
      stages:[{name:L.source,limit:lim(P.gateway_capacity),frac:rin/P.gateway_capacity,pill:spare},
              {name:g.c?L.server_short:L.server,limit:lim(cap),frac:sr/cap,gaugeHot:hot,state:hot?'hot':null,pill:hot?['한도 도달','hot']:null},
              {name:L.dependency,limit:lim(P.database_capacity),frac:sr/P.database_capacity,pill:spare}]});
    o+=K.text(g.W,g.H-2,L.unit,{fs:11,c:C.faint,a:'end'});
    return o;}
  function stats(T){var qv=q(T),sr=served(T),rin=rateIn(T);
    return {left:[['트래픽 ',K.grp(rin),'건/s',rin>cap],['처리 ',K.grp(sr),'건/s',qv>1e-6],['새 요청 대기 ',K.num(qv/cap),'초',qv>1e-6]]};}
  function probe(T){return {queue:Math.round(q(T)*10)/10};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,probe:probe};
};
