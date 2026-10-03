/* Scene: read CPU and P99 together. Three synthetic services, CPU stacked over P99 on one
   time axis per service. Series and event times come from Python; verdicts appear only
   once the event that justifies them has happened. */
CA_SCENES['cpu-latency']=function(D,K,GR){
  var S=D.series,E=D.events,L=D.labels,C=K.C,TP=GR.timePanels,H=D.axes.end;
  function geom(W){var g={W:W,nw:W<560,cols:[]},i,x0,x1,y;
    for(i=0;i<3;i++){if(!g.nw){var cw=(W-40)/3;x0=i*(cw+20);x1=x0+cw;y=0;}else{x0=0;x1=W;y=i*132;}
      var c={x0:x0,x1:x1,top:y+12};c.cpu=TP.panelIn(x0+4,x1-4,c.top+24,g.nw?38:62,H,100);
      c.p99=TP.panelIn(x0+4,x1-4,c.cpu.y+c.cpu.h+(g.nw?20:28),g.nw?38:62,H,D.axes.p99_max);g.cols.push(c);}
    var last=g.cols[2].p99;g.H=last.y+last.h+22;return g;}
  function draw(T,g){var o='';
    D.services.forEach(function(sv,i){var c=g.cols[i],a=c.cpu,b=c.p99,v=sv.verdict;
      o+=K.text(c.x0,c.top,sv.name,{fs:13,c:C.ink,w:700});
      if(v&&T>=v[0]-1e-9)o+=K.text(c.x1,c.top,v[1],{fs:12,c:v[2]==='hot'?C.red:C.amber,a:'end',w:700});
      o+=K.text(c.x0,a.y-5,L.cpu,{fs:11})+K.text(a.x1,a.y-5,K.num(TP.at(S.t,sv.cpu,T),0)+'%',{fs:11,c:C.blue,a:'end',w:700});
      o+=TP.yTicks(K,a,[[100,'']],true)+TP.series(K,a,S.t,sv.cpu,T,C.blue,1.8);
      o+=K.text(c.x0,b.y-5,L.p99,{fs:11})+K.text(b.x1,b.y-5,K.grp(TP.at(S.t,sv.p99,T))+'ms',{fs:11,c:C.purple,a:'end',w:700});
      o+=TP.yTicks(K,b,[[D.axes.p99_max,'']],true)+TP.series(K,b,S.t,sv.p99,T,C.purple,1.8);
      if(!g.nw||i===2)o+=TP.ticksX(K,b,D.axes.x_ticks);
      o+=TP.cursor(K,a,b,T);});
    return o;}
  function stats(T){return {left:[['관찰 ',K.num(Math.min(T,H),0),'/'+K.num(H,0)+'초 (합성)',false]]};}
  function probe(T){return {cpu:D.services.map(function(s){return Math.round(TP.at(S.t,s.cpu,T)*10)/10;}),p99:D.services.map(function(s){return Math.round(TP.at(S.t,s.p99,T)*10)/10;})};}
  return {end:H,geom:geom,draw:draw,stats:stats,probe:probe};
};
