/* Scene kind "trend": metrics on one shared time axis. 1-3 groups (columns >= 560 px, stacked
   below), each with 1-4 panels of 1-3 series. Values, events, thresholds, pills and notes come
   from data (visual_spec.trend_data); names and readings appear only once their time is reached. */
CA_SCENES['trend']=function(D,K,GR){
  var C=K.C,TP=GR.timePanels,end=D.time.end,G=D.groups;
  var PAL={blue:[C.blue,C.blueText,'#e7f5ff'],purple:[C.purple,C.purpleText,C.purpleSoft],green:[C.green,C.greenText,C.greenSoft],
           red:[C.red,C.redText,C.redSoft],amber:[C.amber,C.amberText,C.amberSoft],gray:['#868e96',C.muted,'#f1f3f5']};
  function fmt(v,p){if(!p.unit&&Math.abs(v)>=1000)return (v<0?'−':'')+(Math.abs(v)/1000).toFixed(1)+'k';   /* 7.6k, as on a RPS axis */
    var s=Number(Math.abs(v)).toFixed(p.decimals||0).split('.');
    return (v<0?'−':'')+K.grp(+s[0])+(s[1]?'.'+s[1]:'')+p.unit;}
  function tick(v,p){if(p.unit==='%')return Math.round(v)+'%';if(Math.abs(v)>=1000&&v%500===0)return (v/1000)+'k';   /* 10k, 2.5k */
    return (Math.abs(v)<10&&Math.round(v)!==v?Number(v).toFixed(1):K.grp(v))+(p.unit==='x'?'x':'');}
  function latest(list,T){var r=null;(list||[]).forEach(function(x){if(T>=x[0]-1e-9)r=x;});return r;}
  /* Columns side by side on wide screens (4 groups make a 2 x 2 grid), stacked on phones. */
  function geom(W){var g={W:W,nw:W<560,cols:[]},per=g.nw?1:G.length===4?2:G.length,cols=per>1,y=0,rowB=0;
    G.forEach(function(gr,i){var n=gr.panels.length,ph=cols?(n>2?48:G.length===4?56:62):g.nw?(G.length>1?(n===1&&G.length===2?60:34):n===1?96:n===2?56:44):(n===1?150:n===2?80:60);
      var k=i%per;if(cols&&k===0&&i>0)y=rowB+14;   /* next grid row; stacked columns advance below */
      var cw=cols?(W-18*(per-1))/per:W,x0=cols?k*(cw+18):0,top=y,head=(gr.pill.length?24:0)+(gr.title?24:0)+(D.bands.length?22:0),c={x0:x0,x1:x0+cw,top:top,panels:[]};
      var py=top+head+18;gr.panels.forEach(function(p){c.panels.push(TP.panelIn(x0+36,x0+cw,py,ph,end,p.max));py+=ph+24;
        if(D.stream&&p.label===D.stream.after){var sh=D.stream.side?78:50;c.strip={y:py-4,h:sh,x0:x0+36,x1:x0+cw};py+=sh+20;}});
      c.bottom=py-24+(cols||!g.nw||i===G.length-1?18:0);c.note=c.bottom+16;
      c.axis=cols||i===G.length-1;g.cols.push(c);
      var cb=c.bottom+(gr.note.length&&!g.nw?24:0);rowB=k===0?cb:Math.max(rowB,cb);
      if(!cols)y=c.bottom+(gr.note.length&&!g.nw?24:6)+10;});
    g.H=Math.max.apply(null,g.cols.map(function(c,i){return c.bottom+(G[i].note.length&&!g.nw?24:0);}))+8;
    g.mark=D.labels.data_kind!=='측정값';if(g.mark)g.H+=16;return g;}
  /* Value labels: greedy placement, one label at a time, at the first candidate position (above
     the dot, below it, further out) that touches neither an already placed label nor a fixed
     label (event names); if none is free, the least-overlapping candidate wins. */
  function labels(items,p,fixed){var lo=p.y+11,hi=p.y+p.h-3,placed=(fixed||[]).slice(),o='';   /* stay inside the panel: below it are the axis ticks */
    function box(it,y){var w=K.tw(it.s,12),x0=it.a==='end'?it.x-w:it.x;return {x0:x0-3,x1:x0+w+3,y0:y-14,y1:y+5};}   /* ~1.5em: the rendered text box */
    function hit(b){var s=0;placed.forEach(function(f){var w=Math.min(b.x1,f.x1)-Math.max(b.x0,f.x0),h=Math.min(b.y1,f.y1)-Math.max(b.y0,f.y0);if(w>0&&h>0)s+=w*h;});return s;}
    items.sort(function(a,b){return a.dy-b.dy;}).forEach(function(it){var best=null,bs=1e9;
      var slots=[lo,hi];for(var y=lo;y<=hi;y+=4)slots.push(y);   /* above, below, then any free slot nearest the dot, */
      placed.forEach(function(f){slots.push(f.y0-5,f.y1+14);});   /* including the slots touching a placed label */
      var cand=[it.dy-8,it.dy+16].concat(slots.sort(function(a,b){return Math.abs(a-it.dy)-Math.abs(b-it.dy);}));
      cand.forEach(function(y){if(y<lo||y>hi||bs===0)return;var s=hit(box(it,y))*100;
        placed.forEach(function(f){if(f.dy!=null&&(f.dy-it.dy)*(f.ly-y)<0)s+=1;});   /* keep labels in the order of their dots */
        if(s<bs){bs=s;best=y;}});
      if(best==null||bs>=100)return;   /* no free spot: a value label never sits on another label (the reading is in the table) */
      var b=box(it,best);b.dy=it.dy;b.ly=best;placed.push(b);
      o+=K.text(it.x,best,it.s,{fs:12,c:it.c,a:it.a,w:700,halo:1});});
    return o;}
  function series(pd,nm){for(var i=0;i<pd.series.length;i++)if(pd.series[i].name===nm)return pd.series[i];return null;}
  function panel(p,pd,T,first){var o=K.rect(p.x0,p.y,p.x1-p.x0,p.h,{r:3,fill:C.paper2,st:C.rule}),named=pd.series.filter(function(s){return s.label!==false;}),multi=named.length>1;   /* helper series (label:false) stay out of the legend */
    var lastY=-1e9;pd.ticks.slice().sort(function(a,b){return b-a;}).forEach(function(v){var y=p.Y(v);o+=K.line(p.x0,y,p.x1,y,C.rule);
      if(y-lastY>=14){o+=K.text(p.x0-5,y+3.5,tick(v,pd),{fs:11,c:C.muted,a:'end'});lastY=y;}});   /* labels only where they fit */
    if(!pd.hide)o+=K.text(p.x0,p.y-7,pd.label,{fs:13,c:C.text,w:700});
    /* an interval is shaded once it has ended: the reader sees it as a finding, not a forecast */
    D.bands.forEach(function(b){if(T>=b[1]-1e-9)o+=K.rect(p.X(b[0]),p.y,p.X(b[1])-p.X(b[0]),p.h,{r:0,fill:PAL[b[3]][2],op:.9});});
    D.between.forEach(function(b){if(b[0]!==pd.label||T<b[3])return;var u=series(pd,b[1]),l=series(pd,b[2]),t1=Math.min(T,b[4]),ts=[b[3]];
      u.t.forEach(function(t){if(t>b[3]&&t<t1)ts.push(t);});ts.push(t1);
      var upr=ts.map(function(t){return K.f(p.X(t))+' '+K.f(p.Y(TP.at(u.t,u.v,t)));}),bot=ts.slice().reverse().map(function(t){return K.f(p.X(t))+' '+K.f(p.Y(TP.at(l.t,l.v,t)));});
      o+=K.path('M'+upr.join('L')+'L'+bot.join('L')+'Z',PAL[b[5]][2],'.85');});
    if(multi){var lx=p.x1;named.slice().reverse().forEach(function(s){var w=K.tw(s.name,12)+14;lx-=w;o+=K.rect(lx,p.y-15,9,9,{r:2,fill:PAL[s.color][0]})+K.text(lx+12,p.y-7,s.name,{fs:12,c:C.muted});lx-=6;});}
    var marks=[];
    pd.series.forEach(function(s){var c=PAL[s.color],pts=TP.cut(K,p,s.t,s.v,T);if(pts.length<2||T<s.t[0])return;var last=Math.min(T,s.t[s.t.length-1]),v=TP.at(s.t,s.v,last),x=p.X(last),y=p.Y(v);
      if(!multi&&s.area!==false)o+=K.path('M'+K.f(p.X(s.t[0]))+' '+K.f(p.Y(0))+'L'+pts.join('L')+'L'+K.f(x)+' '+K.f(p.Y(0))+'Z',c[2],'1');
      o+='<path d="M'+pts.join('L')+'" fill="none" stroke="'+c[0]+'" stroke-width="2"'+(s.dashed?' stroke-dasharray="5 4"':'')+' stroke-linejoin="round"/>';
      if(s.dots)s.t.forEach(function(t,k){if(t<=T+1e-9)o+=K.dot(p.X(t),p.Y(s.v[k]),3.5,c[0]);});
      o+=K.ring(x,y,3.5,'#fff',c[0],2);
      if(s.label===false)return;var right=x>p.x1-56;marks.push({x:right?x-6:x+6,y:y-8>=p.y+11?y-8:y+16,dy:y,s:fmt(v,pd),c:c[1],a:right?'end':'start'});});
    if(T<end-1e-6)o+=K.line(p.X(T),p.y,p.X(T),p.y+p.h,C.faint,{d:'2 3'});
    /* thresholds after the series (an area fill must not paint over their label); the label sits
       on the side away from the cursor, where the value labels are */
    var late=p.X(Math.min(T,end))>(p.x0+p.x1)/2;
    D.thresholds.forEach(function(th){if(th[0]!==pd.label)return;var ly=p.Y(th[1]),ty=ly-p.y<18?ly+15:ly-5;   /* near the top edge the label goes under the line */
      o+=K.line(p.x0,ly,p.x1,ly,C.red,{d:'4 3',op:.8})+K.text(late?p.x0+4:p.x1-4,ty,th[2],{fs:12,c:C.redText,a:late?'start':'end',w:700,halo:1});});
    var fixed=first?(p.evBoxes||[]):[];
    /* annotations at a series value, bold and coloured like the series they explain */
    D.annotations.forEach(function(a){if(a[1]!==pd.label||T<a[0]-1e-9)return;var sr=series(pd,a[2]),x=p.X(a[0]),y=p.Y(TP.at(sr.t,sr.v,a[0])),w=K.tw(a[3],13),
        an=x>p.x1-w/2-4?'end':x<p.x0+w/2+4?'start':'middle',x0=an==='end'?x-w:an==='middle'?x-w/2:x,lo=p.y+15,hi=p.y+p.h-5;
      /* preferred side first, then the other, then further out; never on an event label or another annotation */
      var cands=a[5]==='below'?[y+20,y-11,y+36,y-27]:[y-11,y+20,y-27,y+36],ty=null;
      cands.some(function(c){c=Math.max(lo,Math.min(hi,c));var bx={x0:x0-3,x1:x0+w+3,y0:c-15,y1:c+5};
        if(fixed.some(function(f){return Math.min(bx.x1,f.x1)>Math.max(bx.x0,f.x0)&&Math.min(bx.y1,f.y1)>Math.max(bx.y0,f.y0);}))return false;ty=c;return true;});
      if(ty==null)ty=Math.max(lo,Math.min(hi,cands[0]));
      o+=K.text(x,ty,a[3],{fs:13,c:PAL[a[4]][1],a:an,w:700,halo:1});fixed.push({x0:x0-8,x1:x0+w+8,y0:ty-18,y1:ty+8});});   /* generous: value labels must keep clear */
    return o+labels(marks,p,fixed);}
  /* Request stream between two panels: tokens at a steady pace; from each phase on, a share
     (model value) is diverted: up and out (failed fast) or down to a side box (cache miss -> DB). */
  function stream(st,S,T){var o='',my=S.y+16,x0=S.x0,x1=S.x1,bx=(x0+x1)/2,dt=end/30,v=(x1-x0)/(end/5),sy=S.y+S.h-14;
    function phase(t){var r=st.phases[0];st.phases.forEach(function(q){if(t>=q[0]-1e-9)r=q;});return r;}
    o+=K.line(x0,my,x1,my,C.rule,{sw:1.5})+K.text(x0-6,my+4,st.label,{fs:12,c:C.muted,a:'end'});
    if(st.side)o+=K.rect(bx-34,sy-12,68,22,{r:6,fill:C.paper2,st:C.edge})+K.text(bx,sy+3,st.side,{fs:12,c:C.text,a:'middle',w:700});
    var n=Math.ceil((end+(x1-x0)/v)/dt);
    for(var i=0;i<n;i++){var born=i*dt-(x1-x0)/v,ph=phase(Math.max(0,born+(bx-x0)/v)),out=((i*0.6180339)%1)<ph[1]-1e-9,d=(Math.min(T,end)-born)*v;
      if(d<0||born+(x1-x0)/v<0&&false)continue;var x=x0+d,y=my,op=1,col=PAL[ph[2]][0];
      if(out){col=PAL[ph[3]][0];if(x>bx){var e=x-bx;if(st.side){y=my+Math.min(e,sy-12-my);x=bx;if(e>sy-12-my+4)continue;}else{x=bx+e*.6;y=my-e*.45;op=Math.max(0,1-e/90);if(op<=0)continue;}}}
      if(x>x1)continue;o+=K.dot(x,y,4,col,op);}
    if(st.box)o+=K.rect(bx-38,my-11,76,22,{r:11,fill:'#e7f5ff',st:C.blue,sw:1.4})+K.text(bx,my+4,st.box,{fs:12,c:C.blueText,a:'middle',w:700});
    var cur=phase(Math.min(T,end));if(cur[4])o+=K.text(bx+(st.side?44:14),my-12,cur[4],{fs:12,c:PAL[cur[3]][1],a:'start',w:700,halo:1});
    if(st.end_note)o+=K.text(x1,my+20,st.end_note,{fs:12,c:C.blueText,a:'end',halo:1});   /* under the line: the phase note is above */
    return o;}
  function draw(T,g){var o=g.mark?K.text(g.W,g.H-3,D.labels.data_kind,{fs:12,c:C.muted,a:'end'}):'';   /* illustrative/estimated data says so in the picture */
    G.forEach(function(gr,i){var c=g.cols[i],pl=latest(gr.pill,T),nt=latest(gr.note,T),hy=c.top;
      if(gr.title){o+=K.text(c.x0,hy+15,gr.title,{fs:14,c:PAL[gr.color][1],w:700});hy+=24;}
      if(pl)o+=K.pill(c.x0,hy+11,pl[1],pl[2],{a:'start',fs:13});
      var a=c.panels[0],b=c.panels[c.panels.length-1],rows=[];
      /* event labels inside the top panel, each on the first row where it does not touch another */
      var EV=D.events.concat(gr.events||[]);a.evBoxes=[];EV.forEach(function(e){if(T<e[0]-1e-9)return;var x=a.X(e[0]),w=K.tw(e[1],12),right=x+w+6>a.x1,x0=right?x-4-w:x+4,r=0;
        while(rows[r]&&rows[r].some(function(q){return x0<q[1]+6&&x0+w>q[0]-6;}))r++;(rows[r]=rows[r]||[]).push([x0,x0+w]);
        var col=e[2]&&e[2]!=='gray'?PAL[e[2]]:null,ty=a.y+14+r*16;
        e.ty=ty;e.x0=x0;e.right=right;e.col=col;a.evBoxes.push({x0:x0-3,x1:x0+w+3,y0:ty-13,y1:ty+4});});
      gr.panels.forEach(function(pd,j){o+=panel(c.panels[j],pd,T,j===0);});
      if(c.strip)o+=stream(D.stream,c.strip,T);
      /* lines after the panels (a panel background would hide them), labels last */
      EV.forEach(function(e){if(T<e[0]-1e-9)return;var x=a.X(e[0]);o+=K.line(x,a.y,x,b.y+b.h,e.col?e.col[0]:C.ink,{d:'4 3',sw:1.4,op:e.col?.9:.55});});
      EV.forEach(function(e){if(T<e[0]-1e-9)return;o+=K.text(e.x0,e.ty,e[1],{fs:12,c:e.col?e.col[1]:C.text,w:700,halo:1});});
      D.bands.forEach(function(bd){if(T<bd[1]-1e-9)return;var x0=a.X(bd[0]),x1=a.X(bd[1]),y=a.y-26,cl=PAL[bd[3]];
        o+='<path d="M'+K.f(x0)+' '+K.f(y+6)+'V'+K.f(y)+'H'+K.f(x1)+'V'+K.f(y+6)+'" fill="none" stroke="'+cl[0]+'" stroke-width="1.6"/>';
        var bw=K.tw(bd[2],13),cx=(x0+x1)/2,ba=cx+bw/2>g.W-2?'end':cx-bw/2<2?'start':'middle';   /* keep the bracket label inside the figure */
        o+=K.text(ba==='end'?Math.min(x1,g.W-2):ba==='start'?Math.max(x0,2):cx,y-5,bd[2],{fs:13,c:cl[1],a:ba,w:700,halo:1});});
      if(c.axis)o+=TP.ticksX(K,b,D.ticks);
      if(nt&&!g.nw){var cw=c.x1-c.x0-4,nf=13;while(nf>11&&K.tw(nt[1],nf)>cw)nf--;   /* shrink to the column, centred on it */
        o+=K.text((c.x0+c.x1)/2,c.note,nt[1],{fs:nf,c:nt[2]==='hot'?C.redText:nt[2]==='warn'?C.amberText:C.greenText,a:'middle',w:700});}});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {values:G.map(function(gr){return gr.panels.map(function(p){return p.series.map(function(s){return Math.round(TP.at(s.t,s.v,T)*10)/10;});});})};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
