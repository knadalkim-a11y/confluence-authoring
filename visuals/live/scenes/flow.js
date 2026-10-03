/* Scene kind "flow": inflow -> stages with limits -> queue in front of the bottleneck, one lane
   or two variants side by side. All numbers (queue, served, rejected, token times) come from
   the Python fluid model in data (visual_spec.flow_data); this file maps state at T. */
CA_SCENES['flow']=function(D,K,GR){
  var L=D.labels,C=K.C,FQ=GR.flowQueue,TP=GR.timePanels,end=D.time.end,t=D.t,lanes=D.lanes,two=lanes.length>1;
  var per=(L.rate_unit.split('/')[1]||'');
  function at(a,T){return Math.max(0,TP.at(t,a,T));}
  function rateIn(T){var r=D.inflow[0][1];D.inflow.forEach(function(x){if(T>=x[0]-1e-9)r=x[1];});return r;}
  function served(l,T){var i=1;while(i<t.length-1&&t[i]<=T+1e-9)i++;return (l.srv[i]-l.srv[i-1])/(t[i]-t[i-1]);}
  function cap(l){return l.stages[l.b].cap;}
  function waitText(w){return w<1e-6?'0'+L.time_unit:L.time_unit==='초'&&w<1?Math.round(w*1000)+'ms':K.num(w)+L.time_unit;}
  /* Two single-stage variants sit side by side on wide screens; anything else stacks. */
  function geom(W){var g={W:W,nw:W<560,lanes:[]},side=two&&W>=560&&lanes.every(function(l){return l.stages.length===1;}),y=0;
    var lw=side?(W-28)/2:W;
    lanes.forEach(function(l,i){var o={stages:l.stages,queueAt:l.b,lead:l.b>0,tail:true,rows:two?3:2};
      if(l.stages.length===1)o.nodeW=lw<420?68:84;if(l.limit)o.slots=l.limit;
      var c=FQ.chainGeom(lw,two?20:0,o);c.x=side?i*(lw+28):0;c.y=side?0:y;
      /* one lane: a history strip keeps the story visible after the queue drains (print/no-JS) */
      c.hist=!two&&l.peak_q>1e-6;c.h=c.bottom+(two?4+30+34:0)+(c.hist?52:0);g.lanes.push(c);y+=c.h+(two?18:0);});
    g.H=Math.max.apply(null,g.lanes.map(function(c){return c.y+c.h;}))+18;return g;}
  function lane(c,i,T){var l=lanes[i],qv=at(l.q,T),hot=qv>1e-6,o='',multi=l.stages.length>1,rin=rateIn(T),sr=served(l,T);
    var st=l.stages.map(function(s,j){var isB=j===l.b,flow=j<l.b?rin:sr;
      return {name:c.c?s.short:s.name,sub:multi?'':K.grp(s.cap)+(per?'/'+per:''),limit:multi?(c.c?'':'한도 ')+K.grp(s.cap)+(c.c?'':L.rate_unit):'',
        frac:flow/s.cap,gaugeHot:isB&&hot,state:multi&&isB&&hot?'hot':null,pill:multi&&hot?(isB?[L.limit_pill,'hot']:[L.spare,'ok']):null};});
    var cp=null;D.callouts.forEach(function(x){if(x[0]===i&&T>=x[1]-1e-9)cp=[x[2],x[3]];});
    if(two)o+=K.text(0,c.top-8,l.name,{fs:13,c:l.tone==='bad'?C.redText:l.tone==='good'?C.greenText:C.ink,w:700});
    o+=FQ.chainDraw(K,c,{T:T,final:T>=end-1e-9,q:qv,unit:D.unit,tokens:l.tokens,tail:function(x){return at(l.q,x);},v:D.speed,
      qLabel:l.limit?'':K.grp(qv)+L.count_unit+' 대기',qHot:!l.limit&&hot,boxAlways:two,limitLabel:l.limit?L.limit_tag.replace('{limit}',K.grp(l.limit)):'',
      centrePill:cp,stages:st});
    if(two){var ry=c.bottom+4,w=qv/cap(l),rej=at(l.rej,T),ot=null;D.inflow.forEach(function(x){if(ot===null&&x[1]>cap(l))ot=x[0];});
      var over=ot===null||T<=ot?0:at(l.inc,T)-at(l.inc,ot);
      o+=K.rich(0,ry,[['대기 ',null,0],[K.grp(qv)+L.count_unit,hot&&!l.limit?C.redText:C.blueText,1],['  ·  대기 시간 ',null,0],[waitText(w),w>=1?C.redText:C.blueText,1]],{fs:12});
      var done=[[L.served+' ',null,0],[K.grp(at(l.srv,T))+L.count_unit,C.greenText,1]];
      if(l.limit)done=done.concat([['  ·  거부 ',null,0],[K.grp(rej)+L.count_unit,rej>0?C.redText:C.muted,1],[over>1e-6?' ('+K.num(100*rej/over)+'%)':'',rej>0?C.redText:C.muted,1]]);
      o+=K.rich(0,ry+18,done,{fs:12});
      var wv=l.q.map(function(v){return v/cap(l);});
      o+=TP.spark(K,0,c.W,ry+30,30,end,D.axes.wait_max,t,wv,T,l.tone==='good'?C.green:l.tone==='bad'?C.red:C.blue,l.tone==='good'?C.greenSoft:l.tone==='bad'?C.redSoft:C.blueSoft,'');}
    if(c.hist){var hy=c.bottom+8;o+=K.text(0,hy+10,L.history,{fs:11,c:C.text,w:700});
      o+=TP.spark(K,0,c.W,hy+16,28,end,l.peak_q*1.15,t,l.q,T,C.amber,C.amberSoft,'');
      if(T>=l.peak_t-1e-9){var px=c.W*l.peak_t/end,py=hy+16+28-28*l.peak_q/(l.peak_q*1.15);
        o+=K.text(Math.min(c.W-2,Math.max(2,px)),py-4,'최대 '+K.grp(l.peak_q)+L.count_unit,{fs:11,c:C.amberText,a:px>c.W-60?'end':px<60?'start':'middle',w:700,halo:1});}}
    return '<g transform="translate('+K.f(c.x)+','+K.f(c.y)+')">'+o+'</g>';}
  function draw(T,g){var o='';g.lanes.forEach(function(c,i){o+=lane(c,i,T);});return o+K.text(g.W,g.H-2,L.legend,{fs:11,c:C.muted,a:'end'});}
  function stats(T){var rin=rateIn(T),l=lanes[0],qv=at(l.q,T);
    if(!two){var s=[[L.inflow+' ',K.grp(rin),L.rate_unit,rin>cap(l)],[L.served+' ',K.grp(served(l,T)),L.rate_unit,qv>1e-6],[L.wait+' ',K.num(qv/cap(l)),L.time_unit,qv>1e-6]];
      if(l.limit)s.push(['거부 ',K.grp(at(l.rej,T)),L.count_unit,at(l.rej,T)>0]);return {left:s};}
    var caps=lanes.map(cap),same=caps[0]===caps[1];
    return {left:[[L.inflow+' ',K.grp(rin),L.rate_unit,rin>Math.min.apply(null,caps)],['처리 한도 ',same?K.grp(caps[0]):K.grp(caps[0])+' / '+K.grp(caps[1]),L.rate_unit,false]]};}
  function probe(T){return {queue:lanes.map(function(l){return Math.round(at(l.q,T)*10)/10;}),rejected:lanes.map(function(l){return Math.round(at(l.rej,T)*10)/10;})};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
