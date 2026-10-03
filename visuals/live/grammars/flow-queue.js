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
