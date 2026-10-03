/* Scene kind "trend": metrics on one shared time axis. 1-3 groups (columns >= 560 px, stacked
   below), each with 1-4 panels of 1-3 series. Values, events, thresholds, pills and notes come
   from data (visual_spec.trend_data); names and readings appear only once their time is reached. */
CA_SCENES['trend']=function(D,K,GR){
  var C=K.C,TP=GR.timePanels,end=D.time.end,G=D.groups;
  var PAL={blue:[C.blue,C.blueText,'#e7f5ff'],purple:[C.purple,C.purpleText,C.purpleSoft],green:[C.green,C.greenText,C.greenSoft],
           red:[C.red,C.redText,C.redSoft],amber:[C.amber,C.amberText,C.amberSoft],gray:['#868e96',C.muted,'#f1f3f5']};
  function fmt(v,p){var s=Number(Math.abs(v)).toFixed(p.decimals||0).split('.');
    return (v<0?'−':'')+K.grp(+s[0])+(s[1]?'.'+s[1]:'')+p.unit;}
  function tick(v,p){return p.unit==='%'?Math.round(v)+'%':(Math.abs(v)<10&&Math.round(v)!==v?Number(v).toFixed(1):K.grp(v));}
  function latest(list,T){var r=null;(list||[]).forEach(function(x){if(T>=x[0]-1e-9)r=x;});return r;}
  function geom(W){var g={W:W,nw:W<560,cols:[]},cols=!g.nw&&G.length>1,y=0;
    G.forEach(function(gr,i){var n=gr.panels.length,ph=cols?(n>2?48:62):g.nw?(G.length>1?34:n===1?96:n===2?56:44):(n===1?150:n===2?80:60);
      var cw=cols?(W-18*(G.length-1))/G.length:W,x0=cols?i*(cw+18):0,top=cols?0:y,head=gr.pill.length?24:0,c={x0:x0,x1:x0+cw,top:top,panels:[]};
      var py=top+head+18;gr.panels.forEach(function(p){c.panels.push(TP.panelIn(x0+36,x0+cw,py,ph,end,p.max));py+=ph+24;});
      c.bottom=py-24+(cols||!g.nw||i===G.length-1?18:0);c.note=c.bottom+16;
      c.axis=cols||i===G.length-1;g.cols.push(c);y=c.bottom+(gr.note.length&&!g.nw?24:6)+(cols?0:10);});
    g.H=Math.max.apply(null,g.cols.map(function(c,i){return c.bottom+(G[i].note.length&&!g.nw?24:0);}))+8;
    g.mark=D.labels.data_kind!=='측정값';if(g.mark)g.H+=16;return g;}
  /* Value labels: greedy placement, one label at a time, at the first candidate position (above
     the dot, below it, further out) that touches neither an already placed label nor a fixed
     label (event names); if none is free, the least-overlapping candidate wins. */
  function labels(items,p,fixed){var lo=p.y+11,hi=p.y+p.h-3,placed=(fixed||[]).slice(),o='';   /* stay inside the panel: below it are the axis ticks */
    function box(it,y){var w=K.tw(it.s,11),x0=it.a==='end'?it.x-w:it.x;return {x0:x0-3,x1:x0+w+3,y0:y-14,y1:y+5};}   /* ~1.5em: the rendered text box */
    function hit(b){var s=0;placed.forEach(function(f){var w=Math.min(b.x1,f.x1)-Math.max(b.x0,f.x0),h=Math.min(b.y1,f.y1)-Math.max(b.y0,f.y0);if(w>0&&h>0)s+=w*h;});return s;}
    items.sort(function(a,b){return a.dy-b.dy;}).forEach(function(it){var best=null,bs=1e9;
      var slots=[lo,hi];for(var y=lo;y<=hi;y+=4)slots.push(y);   /* above, below, then any free slot nearest the dot, */
      placed.forEach(function(f){slots.push(f.y0-5,f.y1+14);});   /* including the slots touching a placed label */
      var cand=[it.dy-8,it.dy+16].concat(slots.sort(function(a,b){return Math.abs(a-it.dy)-Math.abs(b-it.dy);}));
      cand.forEach(function(y){if(y<lo||y>hi||bs===0)return;var s=hit(box(it,y))*100;
        placed.forEach(function(f){if(f.dy!=null&&(f.dy-it.dy)*(f.ly-y)<0)s+=1;});   /* keep labels in the order of their dots */
        if(s<bs){bs=s;best=y;}});
      if(best==null)best=Math.max(lo,Math.min(hi,it.dy-8));var b=box(it,best);b.dy=it.dy;b.ly=best;placed.push(b);
      o+=K.text(it.x,best,it.s,{fs:11,c:it.c,a:it.a,w:700,halo:1});});
    return o;}
  function panel(p,pd,T,first){var o=K.rect(p.x0,p.y,p.x1-p.x0,p.h,{r:3,fill:C.paper2,st:C.rule}),multi=pd.series.length>1;
    pd.ticks.forEach(function(v){o+=K.line(p.x0,p.Y(v),p.x1,p.Y(v),C.rule)+K.text(p.x0-5,p.Y(v)+3.5,tick(v,pd),{fs:10,c:C.muted,a:'end'});});
    o+=K.text(p.x0,p.y-7,pd.label,{fs:11,c:C.text,w:700});
    if(multi){var lx=p.x1;pd.series.slice().reverse().forEach(function(s){var w=K.tw(s.name,11)+14;lx-=w;o+=K.rect(lx,p.y-15,9,9,{r:2,fill:PAL[s.color][0]})+K.text(lx+12,p.y-7,s.name,{fs:11,c:C.muted});lx-=6;});}
    var marks=[];
    pd.series.forEach(function(s){var c=PAL[s.color],pts=TP.cut(K,p,s.t,s.v,T);if(pts.length<2)return;var last=Math.min(T,s.t[s.t.length-1]),v=TP.at(s.t,s.v,last),x=p.X(last),y=p.Y(v);
      if(!multi)o+=K.path('M'+K.f(p.X(s.t[0]))+' '+K.f(p.Y(0))+'L'+pts.join('L')+'L'+K.f(x)+' '+K.f(p.Y(0))+'Z',c[2],'1');
      o+='<path d="M'+pts.join('L')+'" fill="none" stroke="'+c[0]+'" stroke-width="2" stroke-linejoin="round"/>'+K.ring(x,y,3.5,'#fff',c[0],2);
      var right=x>p.x1-56;marks.push({x:right?x-6:x+6,y:y-8>=p.y+11?y-8:y+16,dy:y,s:fmt(v,pd),c:c[1],a:right?'end':'start'});});
    if(T<end-1e-6)o+=K.line(p.X(T),p.y,p.X(T),p.y+p.h,C.faint,{d:'2 3'});
    /* thresholds after the series (an area fill must not paint over their label); the label sits
       on the side away from the cursor, where the value labels are */
    var late=p.X(Math.min(T,end))>(p.x0+p.x1)/2;
    D.thresholds.forEach(function(th){if(th[0]===pd.label)o+=K.line(p.x0,p.Y(th[1]),p.x1,p.Y(th[1]),C.red,{d:'4 3',op:.8})+K.text(late?p.x0+4:p.x1-4,p.Y(th[1])-4,th[2],{fs:11,c:C.redText,a:late?'start':'end',halo:1});});
    var fixed=first?D.events.filter(function(e){return T>=e[0]-1e-9;}).map(function(e){var x=p.X(e[0])+4;return {x0:x-3,x1:x+K.tw(e[1],11)+3,y0:p.y-2,y1:p.y+17};}):[];
    return o+labels(marks,p,fixed);}
  function draw(T,g){var o=g.mark?K.text(g.W,g.H-3,D.labels.data_kind,{fs:11,c:C.muted,a:'end'}):'';   /* illustrative/estimated data says so in the picture */
    G.forEach(function(gr,i){var c=g.cols[i],pl=latest(gr.pill,T),nt=latest(gr.note,T);
      if(pl)o+=K.pill(c.x0,c.top+11,pl[1],pl[2],{a:'start',fs:12});
      gr.panels.forEach(function(pd,j){o+=panel(c.panels[j],pd,T,j===0);});
      var a=c.panels[0],b=c.panels[c.panels.length-1];
      D.events.forEach(function(e){if(T>=e[0]-1e-9)o+=K.line(a.X(e[0]),a.y,a.X(e[0]),b.y+b.h,C.ink,{d:'3 3',op:.55})+K.text(a.X(e[0])+4,a.y+12,e[1],{fs:11,c:C.text,w:700,halo:1});});
      if(c.axis)o+=TP.ticksX(K,b,D.ticks);
      if(nt&&!g.nw)o+=K.text((a.x0+a.x1)/2,c.note,nt[1],{fs:12,c:nt[2]==='hot'?C.redText:nt[2]==='warn'?C.amberText:C.greenText,a:'middle',w:700});});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {values:G.map(function(gr){return gr.panels.map(function(p){return p.series.map(function(s){return Math.round(TP.at(s.t,s.v,T)*10)/10;});});})};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
