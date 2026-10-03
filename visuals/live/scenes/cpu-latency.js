/* Scene: read CPU and P99 together. Three synthetic services, CPU stacked over P99 on one
   time axis per service (columns >= 560 px, stacked groups below). Series and event times
   come from Python; a pattern's name and reading appear only after the event behind it. */
CA_SCENES['cpu-latency']=function(D,K,GR){
  var S=D.series,L=D.labels,C=K.C,TP=GR.timePanels,H=D.axes.end,PM=D.axes.p99_max;
  function geom(W){var g={W:W,nw:W<560,cols:[]},i,ph=W<560?34:62;
    for(i=0;i<3;i++){var cw=g.nw?W:(W-36)/3,x0=g.nw?0:i*(cw+18),y=g.nw?i*136:0,c={x0:x0,x1:x0+cw,top:y};
      c.cpu=TP.panelIn(x0+32,x0+cw,y+40,ph,H,100);c.p99=TP.panelIn(x0+32,x0+cw,c.cpu.y+ph+24,ph,H,PM);
      c.note=c.p99.y+ph+(g.nw?0:34);g.cols.push(c);}
    var last=g.cols[2];g.H=last.p99.y+last.p99.h+(g.nw?22:46);return g;}
  function latest(list,T){var r=null;(list||[]).forEach(function(x){if(T>=x[0]-1e-9)r=x;});return r;}
  function panel(p,ts,vs,T,color,soft,label,ticks,fmt){var o=K.rect(p.x0,p.y,p.x1-p.x0,p.h,{r:3,fill:C.paper2,st:C.rule});
    ticks.forEach(function(t){o+=K.line(p.x0,p.Y(t[0]),p.x1,p.Y(t[0]),C.rule)+K.text(p.x0-5,p.Y(t[0])+3.5,t[1],{fs:10,c:C.faint,a:'end'});});
    o+=K.text(p.x0,p.y-7,label,{fs:11,c:C.muted,w:700});
    var pts=TP.cut(K,p,ts,vs,T);if(pts.length<2)return o;var last=Math.min(T,ts[ts.length-1]),v=TP.at(ts,vs,last),x=p.X(last),y=p.Y(v);
    o+=K.path('M'+K.f(p.X(ts[0]))+' '+K.f(p.Y(0))+'L'+pts.join('L')+'L'+K.f(x)+' '+K.f(p.Y(0))+'Z',soft,'1');
    o+='<path d="M'+pts.join('L')+'" fill="none" stroke="'+color+'" stroke-width="2" stroke-linejoin="round"/>';
    if(T<H-1e-6)o+=K.line(x,p.y,x,p.y+p.h,C.faint,{d:'2 3'});
    var right=x>p.x1-52;o+=K.ring(x,y,3.5,'#fff',color,2)+K.text(right?x-7:x+7,Math.max(p.y+11,Math.min(p.y+p.h-3,y-5)),fmt(v),{fs:11,c:color,a:right?'end':'start',w:700});
    return o;}
  function draw(T,g){var o='';
    D.services.forEach(function(sv,i){var c=g.cols[i],pl=latest(sv.pill,T),nt=latest(sv.note,T);
      o+=K.pill(c.x0,c.top+11,pl[1],pl[2],{a:'start',fs:12});
      o+=panel(c.cpu,S.t,sv.cpu,T,C.blue,'#e7f5ff',L.cpu,[[100,'100%'],[50,'50%'],[0,'0%']],function(v){return Math.round(v)+'%';});
      o+=panel(c.p99,S.t,sv.p99,T,C.purple,C.purpleSoft,L.p99,[[PM,K.grp(PM)],[PM/2,K.grp(PM/2)],[0,'0']],function(v){return K.grp(v)+'ms';});
      if(!g.nw||i===2)o+=TP.ticksX(K,c.p99,D.axes.x_ticks);
      if(nt&&!g.nw)o+=K.text((c.x0+c.x1)/2+16,c.note,nt[1],{fs:12,c:nt[2]==='hot'?C.redText:nt[2]==='warn'?C.amberText:C.greenText,a:'middle',w:700});});
    return o;}
  function stats(T){return {left:[['관찰 ',K.num(Math.min(T,H),0),'/'+K.num(H,0)+'초 (합성)',false]]};}
  function probe(T){return {cpu:D.services.map(function(s){return Math.round(TP.at(S.t,s.cpu,T)*10)/10;}),p99:D.services.map(function(s){return Math.round(TP.at(S.t,s.p99,T)*10)/10;})};}
  return {end:H,geom:geom,draw:draw,stats:stats,probe:probe};
};
