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
      o+=K.rect(left-8,g.my-9,g.qh-left+16,18,{r:9,fill:C.amberSoft,st:'#ffe8a1'});
      o+=K.text(g.qh+8,g.my-15,st.queueLabel,{fs:12,c:C.amberText,a:'end',w:700});}
    st.queue.forEach(function(pos){if(pos>g.qcap-1)return;o+=K.dot(g.qh-pos*g.step,g.my,4.5,C.amber);});
    st.transit.forEach(function(t){var tx=t.target==null?inX1-4:g.qh-Math.min(t.target,g.qcap-1)*g.step;
      o+=K.dot(tx*t.p,g.my,4.5,C.blue,K.clamp(t.p*4));});
    /* overflow count drawn after dots and tokens so nothing paints over it */
    if(st.queueCount>g.qcap)o+=K.text(g.qh-(g.qcap-1)*g.step,g.my+4,'+'+(st.queueCount-g.qcap+1),{fs:10,c:C.amberText,a:'middle',w:700,halo:1});
    o+=K.rect(g.px,g.py,g.pw,g.ph,{r:8,fill:full?C.hotPaper:C.paper2,st:full?C.red:C.edge,sw:full?1.6:1});
    o+=K.text(g.px,g.py-8,st.poolLabel,{fs:12,c:C.text,w:700});
    o+=K.text(g.px+g.pw,g.py-8,st.used+'/'+st.slots+(g.nw?'':' 사용 중'),{fs:12,c:full?C.redText:C.muted,a:'end',w:full?700:400});
    for(i=0;i<st.slots;i++){var cx=g.px+g.pp+(i%4)*(g.cw+g.gap),cy=g.py+g.pp+Math.floor(i/4)*(g.ch+g.gap),c=st.cells[i];
      if(c){o+=K.rect(cx,cy,g.cw,g.ch,{r:5,fill:c.hot?C.redSoft:C.blue,st:c.hot?C.red:C.blueText,op:.35+.65*c.appear});
        o+=K.rect(cx+4,cy+g.ch-7,(g.cw-8)*c.progress,3,{r:1.5,fill:c.hot?C.red:'#fff'});}
      else{o+=K.rect(cx,cy,g.cw,g.ch,{r:5,fill:C.paper,st:C.edge});if(st.flash[i])o+=K.rect(cx,cy,g.cw,g.ch,{r:5,fill:'none',st:C.green,sw:1.6,op:st.flash[i]});}}
    var c0=g.px+g.pw,c1=g.dbx,sp=g.conn/3,v=st.depSlow?6:42,off=(st.T*v)%sp;
    o+=K.line(c0,g.my,c1,g.my,st.depSlow?C.redRail:C.rail,{sw:1.5});
    for(i=0;i<3;i++){var dx=c0+off+i*sp;if(dx<c1-2)o+=K.dot(dx,g.my,2.4,st.depSlow?C.red:C.blue,.8);}
    o+=K.arrow(c1-2,g.my,C.faint);
    o+=K.rect(g.dbx,g.py,g.dbw,g.ph,{r:8,fill:st.depSlow?C.redSoft:C.paper,st:st.depSlow?C.red:C.green,sw:1.6});
    o+=K.text(g.dbx+g.dbw/2,g.my-6,st.depLabel,{fs:13,c:C.ink,a:'middle',w:700});
    o+=K.text(g.dbx+g.dbw/2,g.my+13,(g.nw?'':'응답 ')+st.depValue,{fs:12,c:st.depSlow?C.redText:C.greenText,a:'middle',w:700});
    return o;}
};
/* Stage chain (rate models): [lead rail] -> stage -> ... -> [tail rail]. A queue sits in the
   gap in front of stage `queueAt` (0 = on the lead rail) and is drawn either as a dot grid
   (one dot = `unit` requests, filled front first) or as `slots` buffer cells (one cell = one
   request). Each stage shows its limit and a utilisation gauge with % below; optional pills
   above. Tokens (one = `unit` requests) come from the model's cumulative curves; all routes
   share one speed so spacing stays even, and tokens pass behind later stages. */
CA_GRAMMARS.flowQueue.chainGeom=function(W,top,o){
  var c=W<420,g={W:W,c:c,o:o,n:o.stages.length};
  g.nodeW=o.nodeW||(c?66:112);g.nh=c?40:46;g.top=top;g.y0=top+24;g.my=g.y0+g.nh/2;
  g.lead=o.lead?(c?18:34):0;g.tail=o.tail?(c?18:34):0;g.gap=c?22:44;
  var rest=W-g.lead-g.tail-g.n*g.nodeW-(g.n-1)*g.gap,x=g.lead,i;
  g.qGap=Math.max(c?70:110,rest+(o.queueAt>0?g.gap:g.lead));
  if(o.queueAt===0){g.lead=g.qGap;x=g.lead;}
  g.sx=[];for(i=0;i<g.n;i++){if(i>0)x+=(i===o.queueAt?g.qGap:g.gap);g.sx.push(x);x+=g.nodeW;}
  g.end=g.sx[g.n-1]+g.nodeW+g.tail;
  var qL=o.queueAt===0?(c?34:48):g.sx[o.queueAt-1]+g.nodeW;g.qx0=qL+(c?8:12);g.qx1=g.sx[o.queueAt]-(c?10:14);
  g.rows=o.rows||2;g.pitch=c?11:13;g.cols=Math.max(1,Math.floor((g.qx1-g.qx0-8)/g.pitch));
  if(o.slots){g.cell=Math.min(c?16:20,(g.qx1-g.qx0-8)/o.slots-3);g.qx0=g.qx1-o.slots*(g.cell+3)-5;}
  g.boxH=o.slots?g.cell+10:g.rows*g.pitch+8;
  g.bottom=g.y0+g.nh+50;return g;};
/* st: {T, q, unit, tokens:[[arrive, served|null, rejected]], tail(t)->q, v (px/s),
        stages:[{name, limit, frac, state:'hot'|'ok'|null, pill:[text,kind]|null}],
        qLabel, qHot, boxAlways, centrePill:[text,kind]|null, limitLabel, final (skip tokens)} */
CA_GRAMMARS.flowQueue.chainDraw=function(K,g,st){
  var C=K.C,o='',T=st.T,my=g.my,i,qs=g.sx[g.o.queueAt],v=st.v,x0=0;
  /* rails + arrows */
  var pts=[x0];for(i=0;i<g.n;i++){pts.push(g.sx[i]);pts.push(g.sx[i]+g.nodeW);}pts.push(g.end);
  for(i=0;i<pts.length;i+=2){if(pts[i+1]-pts[i]>2){o+=K.line(pts[i],my,pts[i+1]-2,my,C.rail,{sw:1.5});if(i>0||g.o.lead)o+=K.arrow(pts[i+1]-2,my,C.faint);}}
  /* queue area */
  var busy=st.q>1e-6,showBox=st.boxAlways||busy,bx=g.qx0,bw=g.qx1-g.qx0,by=my-g.boxH/2;
  if(showBox)o+=K.rect(bx,by,bw,g.boxH,{r:6,fill:st.qHot?C.redSoft:C.paper2,st:st.qHot?C.red:C.edge,sw:st.qHot?1.2:1,d:st.qHot&&!g.o.slots?'4 3':null});
  if(g.o.slots){var n=Math.round(st.q);for(i=0;i<g.o.slots;i++){var cx=g.qx1-5-(i+1)*(g.cell+3)+3;
      o+=i<n?K.rect(cx,my-g.cell/2,g.cell,g.cell,{r:4,fill:C.amberCell,st:C.amber}):K.rect(cx,my-g.cell/2,g.cell,g.cell,{r:4,fill:C.paper,st:C.edge});}}
  else if(busy){var cap=g.rows*g.cols,dots=Math.min(cap,Math.ceil(st.q/st.unit-1e-6));
    for(i=0;i<dots;i++){var col=Math.floor(i/g.rows),row=i%g.rows;o+=K.dot(g.qx1-4-g.pitch/2-col*g.pitch,by+4+g.pitch/2+row*g.pitch,g.c?3.6:4.2,C.amber);}}
  if(busy&&st.qLabel)o+=K.text(bx+bw/2,by-7,st.qLabel,{fs:12,c:st.qHot?C.redText:C.amberText,a:'middle',w:700,halo:1});
  if(st.limitLabel)o+=K.line(bx,by-4,bx,by+g.boxH+4,C.red,{d:'3 3',sw:1.2})+K.text(bx+4,by-7,st.limitLabel,{fs:11,c:C.redText,w:700});
  /* tokens (not in the final/static scene: a frozen token reads as a glitch in print) */
  if(!st.final)st.tokens.forEach(function(k){var a=k[0],s=k[1],rej=k[2],tx=rej||st.tail(a)>1e-6?bx:qs,d=tx-x0,ta=a-d/v;
    if(T>=ta&&T<a)o+=K.dot(x0+(T-ta)*v,my,g.c?3.6:4.2,C.blue,K.clamp((T-ta)*v/14));
    if(rej&&T>=a&&T<a+0.35){var r=(T-a)/0.35;o+=K.dot(bx-2-r*8,my-6-r*20,3.6,C.red,1-r);}
    if(s!=null){var sx=g.sx[g.o.queueAt]+g.nodeW,ex=g.end-4;if(T>=s&&T<s+(ex-sx)/v)o+=K.dot(sx+(T-s)*v,my,g.c?3.4:4,C.blue,K.clamp((ex-sx-(T-s)*v)/12));}});
  /* stages */
  st.stages.forEach(function(sg,j){var x=g.sx[j],w=g.nodeW,hot=sg.state==='hot',ok=sg.state==='ok';
    o+=K.rect(x,g.y0,w,g.nh,{r:8,fill:hot?C.hotPaper:C.paper,st:hot?C.red:ok?C.green:C.edge,sw:hot||ok?1.6:1.2});
    o+=K.text(x+w/2,my+(sg.sub?-4:4.5),sg.name,{fs:g.c?12:13,c:hot?C.redText:C.ink,a:'middle',w:700});
    if(sg.sub)o+=K.text(x+w/2,my+14,sg.sub,{fs:11,c:hot?C.redText:ok?C.greenText:C.muted,a:'middle',w:700});
    o+=K.text(x+w/2,g.y0+g.nh+15,sg.limit,{fs:11,c:C.muted,a:'middle'});
    o+=K.gauge(x+4,g.y0+g.nh+22,w-8,sg.frac,sg.gaugeHot);
    if(sg.pill)o+=K.pill(x+w/2,g.top+10,sg.pill[0],sg.pill[1]);});
  /* Over a dot grid the pill may cover dots (they are a mass); over buffer slots it goes below so the
     reader can still count the occupied cells. */
  if(st.centrePill)o+=K.pill(bx+bw/2,g.o.slots?by+g.boxH+14:my,st.centrePill[0],st.centrePill[1],{fs:12});
  return o;};
