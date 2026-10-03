/* Scene: unbounded vs bounded queue under the same overload. Both lanes and the token
   schedule come from the Python fluid model; both lanes share one request-count scale. */
CA_SCENES['bounded-queue']=function(D,K,GR){
  var P=D.params,S=D.series,L=D.labels,C=K.C,FQ=GR.flowQueue,TP=GR.timePanels,cap=P.capacity;
  function at(v,T){return Math.max(0,TP.at(S.t,v,T));}
  function rateIn(T){return T<P.change_time-1e-9?P.before_rate:P.after_rate;}
  function geom(W){var g={W:W},nw=W<560;g.nw=nw;g.u=FQ.laneGeom(W,24,{below:true});g.b=FQ.laneGeom(W,g.u.bottom+32,{reject:true,below:true});
    g.A=TP.panelIn(nw?30:38,W-4,g.b.bottom+46,nw?64:72,P.horizon,D.axes.wait_max);g.H=g.A.y+g.A.h+22;return g;}
  function lane(g,T,qv,tokens,rej,limit){var hot=qv>1e-6;
    return FQ.laneDraw(K,g,{T:T,q:qv,qScale:D.axes.q_max,limit:limit,rejected:rej,rejectLabel:'거부 '+K.grp(rej)+'건',
      qLabel:'대기 '+K.grp(qv)+'건'+(limit!=null&&qv>=limit-1e-6?' (상한)':''),inflowLabel:L.inflow+' '+K.grp(rateIn(T))+'건/s',
      srvName:L.server,srvValue:'한도 '+K.grp(cap)+(g.nw?'':'건/s'),srvFrac:hot?1:rateIn(T)/cap,srvHot:hot,
      exitLabel:'처리 '+K.grp(at(S.srv,T))+'건',tokens:tokens,tail:function(t){return at(limit==null?S.qu:S.qb,t);},TR:0.45,tokenRate:Math.max(P.before_rate,P.after_rate)/D.unit});}
  function draw(T,g){var o='',A=g.A;
    o+=K.rect(0,2,9,9,{r:2,fill:C.red,op:.75})+K.text(13,10,L.lane_u,{fs:12,c:C.ink,w:700})+K.text(g.W,10,L.unit,{fs:11,c:C.faint,a:'end'});
    o+=lane(g.u,T,at(S.qu,T),D.tokens_u,0,null);
    o+=K.rect(0,g.b.top-22,9,9,{r:2,fill:C.green,op:.75})+K.text(13,g.b.top-14,L.lane_b,{fs:12,c:C.ink,w:700});
    o+=lane(g.b,T,at(S.qb,T),D.tokens_b,at(S.rej,T),P.queue_limit);
    o+=TP.title(K,A,L.panel,[[L.legend_u,C.red],[L.legend_b,C.green]]);
    o+=TP.yTicks(K,A,[[0,'0'],[D.axes.wait_max/2,K.num(D.axes.wait_max/2,0)],[D.axes.wait_max,K.num(D.axes.wait_max,0)]],true);
    o+=TP.series(K,A,S.t,S.qu.map(function(v){return v/cap;}),T,C.red,2)+TP.series(K,A,S.t,S.qb.map(function(v){return v/cap;}),T,C.green,2);
    if(T>=P.change_time)o+=TP.mark(K,A,A,P.change_time,L.change,C.amber);
    o+=TP.xAxis(K,A,D.axes.x_step,'초')+TP.cursor(K,A,A,T);
    return o;}
  function stats(T){var rin=rateIn(T),d=rin-cap,over=at(S.inc,T)-at(S.inc,P.change_time),r=at(S.rej,T);
    return {left:[['과부하 구간 거부율 ',over>1e-6?K.num(100*r/over):'-',over>1e-6?'%':'',r>1e-6]],
      right:['유입 − 처리 = ',K.grp(rin)+' − '+K.grp(cap),' = ',d>0?K.grp(d)+'건/s 초과':K.grp(-d)+'건/s 여유',d>0]};}
  function probe(T){return {queue_unbounded:Math.round(at(S.qu,T)*10)/10,queue_bounded:Math.round(at(S.qb,T)*10)/10,rejected:Math.round(at(S.rej,T)*10)/10};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,probe:probe};
};
