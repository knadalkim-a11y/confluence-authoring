/* Scene: unbounded vs bounded queue under the same overload, side by side (stacked below
   560 px). Lanes, token schedule and wait times come from the Python fluid model. */
CA_SCENES['bounded-queue']=function(D,K,GR){
  var P=D.params,S=D.series,L=D.labels,E=D.events,C=K.C,FQ=GR.flowQueue,TP=GR.timePanels,cap=P.capacity;
  function at(v,T){return Math.max(0,TP.at(S.t,v,T));}
  function rateIn(T){return T<P.change_time-1e-9?P.before_rate:P.after_rate;}
  var waitU=S.qu.map(function(v){return v/cap;}),waitB=S.qb.map(function(v){return v/cap;});
  function geom(W){var g={W:W,nw:W<560},lw=g.nw?W:(W-28)/2,i;g.lanes=[];
    var y=0;for(i=0;i<2;i++){var o={stages:[0],queueAt:0,tail:true,rows:3,nodeW:lw<420?68:84};if(i===1)o.slots=P.queue_limit;
      var c=FQ.chainGeom(lw,20,o);c.x=g.nw?0:i*(lw+28);c.y=g.nw?y:0;c.h=c.bottom+4+30+34;g.lanes.push(c);y+=c.h+18;}
    g.H=Math.max(g.lanes[0].y+g.lanes[0].h,g.lanes[1].y+g.lanes[1].h)+16;return g;}
  function lane(c,i,T){var bounded=i===1,qv=at(bounded?S.qb:S.qu,T),hot=qv>1e-6,o='',sr=hot?cap:Math.min(cap,rateIn(T));
    var cp=null;if(!bounded&&E.t_wait1!=null&&T>=E.t_wait1)cp=[L.pill_u,'hot'];if(bounded&&E.t_full!=null&&T>=E.t_full)cp=[L.pill_b,'ok'];
    o+=K.text(0,c.top-8,bounded?L.lane_b:L.lane_u,{fs:13,c:bounded?C.greenText:C.redText,w:700});
    o+=FQ.chainDraw(K,c,{T:T,final:T>=P.horizon-1e-9,q:qv,unit:D.unit,tokens:bounded?D.tokens_b:D.tokens_u,tail:function(t){return at(bounded?S.qb:S.qu,t);},v:D.speed,
      qLabel:bounded?'':K.grp(qv)+'건 대기',qHot:!bounded&&hot,boxAlways:true,limitLabel:bounded?L.limit:'',centrePill:cp,
      stages:[{name:L.server,sub:K.grp(cap)+'/s',limit:'',frac:sr/cap,gaugeHot:false,state:'ok'}]});
    var ry=c.bottom+4,w=qv/cap,rej=at(S.rej,T),over=at(S.inc,T)-at(S.inc,P.change_time);
    o+=K.rich(0,ry,[['대기 ',null,0],[K.grp(qv)+'건',hot&&!bounded?C.redText:C.blueText,1],['  ·  대기 시간 ',null,0],[w<1?Math.round(w*1000)+'ms':K.num(w)+'초',w>=1?C.redText:C.blueText,1]],{fs:12});
    var done=[['처리 ',null,0],[K.grp(at(S.srv,T))+'건',C.greenText,1]];
    if(bounded)done=done.concat([['  ·  거부 ',null,0],[K.grp(rej)+'건',rej>0?C.redText:C.muted,1],[over>1e-6?' ('+K.num(100*rej/over)+'%)':'',rej>0?C.redText:C.muted,1]]);
    o+=K.rich(0,ry+18,done,{fs:12});var sy=ry+30;
    o+=TP.spark(K,0,c.W,sy,30,P.horizon,D.axes.wait_max,S.t,bounded?waitB:waitU,T,bounded?C.green:C.red,bounded?C.greenSoft:C.redSoft,'');
    return '<g transform="translate('+K.f(c.x)+','+K.f(c.y)+')">'+o+'</g>';}
  function draw(T,g){return lane(g.lanes[0],0,T)+lane(g.lanes[1],1,T)+K.text(g.W,g.H-2,L.unit,{fs:11,c:C.muted,a:'end'});}
  function stats(T){var rin=rateIn(T),over=at(S.inc,T)-at(S.inc,P.change_time),r=at(S.rej,T);
    return {left:[['유입 ',K.grp(rin),'건/s',rin>cap],['처리 한도 ',K.grp(cap),'건/s',false]]};}
  function probe(T){return {queue_unbounded:Math.round(at(S.qu,T)*10)/10,queue_bounded:Math.round(at(S.qb,T)*10)/10,rejected:Math.round(at(S.rej,T)*10)/10};}
  return {end:P.horizon,geom:geom,draw:draw,stats:stats,probe:probe};
};
