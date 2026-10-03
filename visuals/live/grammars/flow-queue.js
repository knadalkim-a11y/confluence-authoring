/* Grammar: inflow -> FIFO queue -> fixed worker pool -> dependency.
   One straight inflow route is used for both the visible rail and every moving token.
   Input state is already computed by the scene from the model; this draws only. */
CA_GRAMMARS.flowQueue={
  geom:function(W,top){
    var nw=W<560,g={W:W,nw:nw};
    g.cw=nw?Math.max(24,Math.floor((W*0.42-30)/4)):46;g.ch=nw?24:30;g.gap=nw?4:6;g.pp=nw?6:8;
    g.pw=4*g.cw+3*g.gap+2*g.pp;g.ph=2*g.ch+g.gap+2*g.pp;g.dbw=nw?62:104;g.conn=nw?22:52;
    g.dbx=W-g.dbw;g.px=g.dbx-g.conn-g.pw;g.py=top;g.my=g.py+g.ph/2;
    g.qh=g.px-14;g.step=nw?11:13;g.qmin=nw?30:40;g.qcap=Math.max(3,Math.floor((g.qh-g.qmin)/g.step)+1);
    g.bottom=g.py+g.ph;return g;},
  /* st: {inflowLabel, poolLabel, used, slots, cells:[{hot,progress,appear}|null], flash:[0..1],
          queue:[pos float], queueCount, transit:[{p,target}], depLabel, depValue, depSlow, T} */
  draw:function(K,g,st){
    var C=K.C,o='',i,full=st.used===st.slots,inX1=g.px;
    o+=K.line(0,g.my,inX1-6,g.my,C.rail,{sw:1.5});
    o+='<path d="M'+K.f(inX1-7)+' '+K.f(g.my-4)+'L'+K.f(inX1-1)+' '+K.f(g.my)+'L'+K.f(inX1-7)+' '+K.f(g.my+4)+'" fill="none" stroke="'+C.rail+'" stroke-width="1.5"/>';
    o+=K.text(0,g.my+20,st.inflowLabel,{fs:11});
    if(st.queueCount){var shown=Math.min(st.queueCount,g.qcap),left=g.qh-(shown-1)*g.step;
      o+=K.rect(left-8,g.my-9,g.qh-left+16,18,{r:9,fill:C.amberSoft,op:.55});
      o+=K.text(g.qh+8,g.my-15,st.queueLabel,{fs:12,c:C.amber,a:'end',w:700});}
    st.queue.forEach(function(pos){if(pos>g.qcap-1)return;o+=K.dot(g.qh-pos*g.step,g.my,4.5,C.blue);});
    if(st.queueCount>g.qcap)o+=K.text(g.qh-(g.qcap-1)*g.step,g.my+4,'+'+(st.queueCount-g.qcap+1),{fs:10,c:C.amber,a:'middle',w:700});
    st.transit.forEach(function(t){var tx=t.target==null?inX1-4:g.qh-Math.min(t.target,g.qcap-1)*g.step;
      o+=K.dot(tx*t.p,g.my,4.5,C.blue,K.clamp(t.p*4));});
    o+=K.rect(g.px,g.py,g.pw,g.ph,{r:8,fill:full?C.hotPaper:C.paper2,st:full?C.red:C.edge,sw:full?1.5:1});
    o+=K.text(g.px,g.py-8,st.poolLabel,{fs:12,c:C.ink,w:700});
    o+=K.text(g.px+g.pw,g.py-8,st.used+'/'+st.slots+(g.nw?'':' 사용 중'),{fs:12,c:full?C.red:C.muted,a:'end',w:full?700:400});
    for(i=0;i<st.slots;i++){var cx=g.px+g.pp+(i%4)*(g.cw+g.gap),cy=g.py+g.pp+Math.floor(i/4)*(g.ch+g.gap),c=st.cells[i];
      if(c){o+=K.rect(cx,cy,g.cw,g.ch,{fill:c.hot?C.redSoft:C.blueSoft,st:c.hot?C.red:C.blue,op:.35+.65*c.appear});
        o+=K.rect(cx+4,cy+g.ch-7,(g.cw-8)*c.progress,3,{r:1.5,fill:c.hot?C.red:C.blue});}
      else{o+=K.rect(cx,cy,g.cw,g.ch,{fill:C.paper,st:'#d5dce4'});if(st.flash[i])o+=K.rect(cx,cy,g.cw,g.ch,{fill:C.green,op:st.flash[i]*.25});}}
    var c0=g.px+g.pw,c1=g.dbx,sp=g.conn/3,v=st.depSlow?6:42,off=(st.T*v)%sp;
    o+=K.line(c0,g.my,c1,g.my,st.depSlow?C.redRail:C.rail,{sw:1.5});
    for(i=0;i<3;i++){var dx=c0+off+i*sp;if(dx<c1-2)o+=K.dot(dx,g.my,2.4,st.depSlow?C.red:C.blue,.8);}
    o+=K.rect(g.dbx,g.py,g.dbw,g.ph,{r:8,fill:st.depSlow?C.redSoft:C.paper,st:st.depSlow?C.red:C.edge,sw:st.depSlow?1.5:1});
    o+=K.text(g.dbx+g.dbw/2,g.my-6,st.depLabel,{fs:13,c:C.ink,a:'middle',w:700});
    o+=K.text(g.dbx+g.dbw/2,g.my+13,(g.nw?'':'응답 ')+st.depValue,{fs:12,c:st.depSlow?C.red:C.muted,a:'middle',w:st.depSlow?700:400});
    return o;}
};
/* Fluid lane variant of the same idea (inflow -> queue -> server [-> dependency]) for
   rate models: the queue is a bar on a request-count scale, stages show utilization of
   their limit, and one token stands for `unit` requests derived from the model's
   cumulative curves. Optional reject branch for a bounded queue. */
CA_GRAMMARS.flowQueue.laneGeom=function(W,top,o){
  var nw=W<560,g={W:W,nw:nw,o:o};
  g.nh=nw?50:58;g.top=top;g.my=top+g.nh/2;
  g.srcW=o.source?(nw?64:100):0;g.srvW=nw?70:112;g.depW=o.dep?(nw?64:100):0;
  g.conn=o.dep?(nw?22:52):(nw?54:96);
  g.depX=W-g.depW;g.srvX=g.depX-g.conn-g.srvW;g.srvR=g.srvX+g.srvW;g.x0=g.srcW;
  g.qx1=g.srvX-8;g.qx0=g.x0+(o.source?14:6);g.qL=(g.qx1-g.qx0)*0.82;
  g.binW=nw?92:110;g.binH=24;g.binY=g.my+34;
  g.bottom=o.reject?g.binY+g.binH:g.top+g.nh+(o.below?20:0);return g;};
/* st: {T, q, qScale, limit|null, qLabel, srcName, srcValue, srcFrac, srvName, srvValue, srvFrac,
        srvHot, srvNote, depName, depValue, depFrac, depNote, exitLabel, inflowLabel,
        tokens:[[arrive, served|null, rejected]], tail:fn(t)->q, TR (max travel s), tokenRate (tokens/s), rejectLabel} */
CA_GRAMMARS.flowQueue.laneDraw=function(K,g,st){
  var C=K.C,o='',px=g.qL/st.qScale,T=st.T,my=g.my,start=g.x0,xe=null,bx=0;
  /* One speed for every token route; shorten travel time when tokens would crowd (>= 12 px apart). */
  var TR=st.tokenRate?Math.min(st.TR,(g.qx1-start)/(12*st.tokenRate)):st.TR,v=(g.qx1-start)/TR,exitEnd=g.o.dep?g.depX:g.srvR+g.conn-4,TX=(exitEnd-g.srvR)/v;
  function node(x,w,name,value,frac,hot,note,noteHot){var s='';
    s+=K.rect(x,g.top,w,g.nh,{r:8,fill:hot?C.hotPaper:C.paper2,st:hot?C.red:C.edge,sw:hot?1.5:1});
    s+=K.text(x+w/2,g.top+(g.nw?17:20),name,{fs:g.nw?12:13,c:C.ink,a:'middle',w:700});
    s+=K.text(x+w/2,g.top+(g.nw?31:36),value,{fs:11,c:C.muted,a:'middle'});
    var gy=g.top+g.nh-(g.nw?10:12);s+=K.rect(x+8,gy,w-16,4,{r:2,fill:C.rule});
    s+=K.rect(x+8,gy,(w-16)*K.clamp(frac),4,{r:2,fill:hot?C.red:C.blue});
    if(note)s+=K.text(x+w/2,g.top+g.nh+14,note,{fs:11,c:noteHot?C.red:C.green,a:'middle',w:700});
    return s;}
  function tailX(q){return g.qx1-q*px;}
  o+=K.line(start,my,g.srvX-6,my,C.rail,{sw:1.5});
  o+='<path d="M'+K.f(g.srvX-7)+' '+K.f(my-4)+'L'+K.f(g.srvX-1)+' '+K.f(my)+'L'+K.f(g.srvX-7)+' '+K.f(my+4)+'" fill="none" stroke="'+C.rail+'" stroke-width="1.5"/>';
  if(st.limit!=null){xe=tailX(st.limit);bx=Math.max(0,Math.min(g.srvX-g.binW,xe-g.binW*0.7));
    var hot=st.rejected>0,TJ=Math.hypot(bx+g.binW/2-xe,g.binY-my-6)/v;o+=K.line(xe,my+6,bx+g.binW/2,g.binY,hot?C.redRail:C.rail,{sw:1.5});
    o+=K.rect(bx,g.binY,g.binW,g.binH,{r:6,fill:hot?C.redSoft:C.paper,st:hot?C.red:C.edge});
    o+=K.text(bx+g.binW/2,g.binY+16,st.rejectLabel,{fs:12,c:hot?C.red:C.muted,a:'middle',w:hot?700:400});}
  if(st.q>1e-6){var x=tailX(st.q);o+=K.rect(x,my-7,g.qx1-x,14,{r:3,fill:C.amberSoft,st:C.amber,sw:1});
    o+=K.text(g.qx1,my-13,st.qLabel,{fs:12,c:C.amber,a:'end',w:700});}
  if(!g.o.source&&st.inflowLabel)o+=K.text(0,my+20,st.inflowLabel,{fs:11});
  st.tokens.forEach(function(k){var a=k[0],s=k[1],rej=k[2];
    if(T>=a-TR&&T<a){var p=(T-(a-TR))/TR,tx=rej?xe:(st.tail(a)>1e-6?tailX(st.tail(a)):g.srvX-4);
      o+=K.dot(start+(tx-start)*p,my,4,C.blue,K.clamp(p*4));}
    else if(rej&&T>=a&&T<a+TJ){var r=(T-a)/TJ,ex=bx+g.binW/2;o+=K.dot(xe+(ex-xe)*r,my+6+(g.binY-my-6)*r,4,C.red,1-r*0.4);}
    if(s!=null&&T>=s&&T<s+TX){var e=(T-s)/TX;o+=K.dot(g.srvR+(exitEnd-g.srvR)*e,my,3.5,C.green,0.9);}});
  if(st.srcName)o+=node(0,g.srcW,st.srcName,st.srcValue,st.srcFrac,false);
  o+=node(g.srvX,g.srvW,st.srvName,st.srvValue,st.srvFrac,st.srvHot,st.srvNote,st.srvHot);
  if(g.o.dep){o+=K.line(g.srvR,my,g.depX,my,C.rail,{sw:1.5});o+=node(g.depX,g.depW,st.depName,st.depValue,st.depFrac,false,st.depNote,false);}
  else{o+=K.line(g.srvR,my,g.srvR+g.conn,my,C.rail,{sw:1.5});o+=K.text(g.W,g.top+g.nh+14,st.exitLabel,{fs:11,c:C.green,a:'end',w:700});}
  return o;};
