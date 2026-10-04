/* Scene: Node.js event loop. Tasks (arrival, start, end) and I/O hand-offs come from the Python
   model (mechanism_scenes.event_model): queued requests wait left, the single loop runs one at a
   time, I/O goes down to the thread pool and returns as a callback, and a CPU task stops the loop. */
CA_SCENES['eventloop']=function(D,K,GR){
  var C=K.C,TK=D.tasks,IO=D.io,end=D.end_h;
  function state(T){var q=[],act=null,done=0;TK.forEach(function(t){if(t[3]!=='cpu'&&t[0]<=T&&T<t[1])q.push(t);if(t[1]<=T&&T<t[2])act=t;if((t[3]==='normal'||t[3]==='callback')&&t[2]<=T)done++;});
    q.sort(function(a,b){return a[0]-b[0];});return {q:q,act:act,done:done};}
  function geom(W){var g={W:W,nw:W<560};g.cx=W/2;g.cy=g.nw?118:116;g.r=g.nw?50:62;g.bx=g.cx-g.r-34;g.bw=2*(g.r+34);g.by=g.cy-g.r-30;g.bh=2*g.r+46;
    g.qx=g.bx-24;g.ox=g.bx+g.bw+24;g.lib={x:g.cx-(g.nw?80:90),y:g.by+g.bh+30,w:g.nw?160:180,h:30};g.lag=g.lib.y+g.lib.h+32;g.H=g.lag+14;return g;}
  function draw(T,g){var o='',s=state(T),cpu=s.act&&s.act[3]==='cpu',cy=g.cy,cx=g.cx;
    o+=K.text(g.nw?0:g.qx-110,16,'대기 큐',{fs:13,c:C.text,w:700})+K.text(g.W,16,'응답',{fs:13,c:C.text,a:'end',w:700})+K.text(g.W,34,s.done+'건 완료',{fs:12,c:C.muted,a:'end'});
    /* rails */
    o+=K.line(0,cy,g.bx-4,cy,C.edge,{d:'3 4',sw:1.4})+K.arrow(g.bx-4,cy,C.faint)+K.line(g.bx+g.bw+4,cy,g.W-4,cy,C.edge,{d:'3 4',sw:1.4})+K.arrow(g.W-4,cy,C.faint);
    o+=K.line(cx,g.by+g.bh,cx,g.lib.y,C.edge,{d:'3 3'});
    /* process box and loop */
    o+=K.rect(g.bx,g.by,g.bw,g.bh,{r:10,fill:'#fff',st:C.faint,d:'5 4'})+K.text(cx,g.by+18,'Node.js 프로세스 (싱글 스레드)',{fs:12,c:C.text,a:'middle',w:700});
    o+=K.ring(cx,cy+6,g.r,cpu?C.redSoft:'#f1f7ff',cpu?C.red:'#74a7e6',2.5);   /* a light track: the moving dots carry the motion */if(!cpu)o+=K.text(cx,cy+11,'이벤트 루프',{fs:13,c:C.blueText,a:'middle',w:700});   /* a CPU task takes the loop's place */
    /* queue: oldest nearest the loop */
    s.q.forEach(function(t,k){var x=g.bx-16-k*13;if(x>8)o+=K.dot(x,cy,5,C.blue);});
    if(s.q.length>Math.floor((g.bx-24)/13))o+=K.text(10,cy-12,'+'+s.q.length,{fs:11,c:C.blueText,w:700});
    /* arrivals slide in */
    TK.forEach(function(t){if(t[3]!=='normal')return;var f=(T-(t[0]-.25))/.25;if(f>=0&&f<1)o+=K.dot((g.bx-16)*f,cy,5,C.blue,f*2);});
    /* running task travels the loop */
    /* the loop turns at a steady pace and freezes while the CPU task holds it (no spin per task) */
    var run=Math.min(T,D.a)+Math.max(0,T-D.b),ang=Math.PI+run*2*Math.PI/1.8,busy=!!s.act||s.q.length>0;
    for(var k2=1;k2<=6;k2++){var ta=ang-k2*.09;o+=K.dot(cx+g.r*Math.cos(ta),cy+6+g.r*Math.sin(ta),3.2-k2*.35,cpu?C.red:C.blue,.5-k2*.07);}   /* fading trail */
    o+=K.dot(cx+g.r*Math.cos(ang),cy+6+g.r*Math.sin(ang),6,cpu?C.red:C.blue);
    if(busy&&!cpu){var a2=ang+Math.PI*.9;o+=K.dot(cx+g.r*Math.cos(a2),cy+6+g.r*Math.sin(a2),4.5,C.blue,.85);}
    if(cpu){var w=g.bw-20;o+=K.rect(cx-w/2,cy-20,w,48,{r:6,fill:C.red,st:C.redText})+K.text(cx,cy-1,'CPU 작업 '+K.num(s.act[2]-s.act[1],1)+'s',{fs:13,c:'#fff',a:'middle',w:700})+K.text(cx,cy+20,D.cpu_label,{fs:11,c:'#fff',a:'middle'});}
    /* I/O down to the pool and back */
    IO.forEach(function(x){if(T>=x[0]&&T<x[2]){var down=T<x[1],f3=down?K.clamp((T-x[0])/.25):1;o+=K.dot(cx+8,g.by+g.bh+(g.lib.y-g.by-g.bh)*f3,4.5,C.amber);}});
    o+=K.rect(g.lib.x,g.lib.y,g.lib.w,g.lib.h,{r:6,fill:C.paper2,st:C.edge})+K.text(cx,g.lib.y+20,'OS / libuv 스레드 풀',{fs:12,c:C.muted,a:'middle'});
    /* responses leave right */
    TK.forEach(function(t){if(t[3]!=='normal'&&t[3]!=='callback')return;var f4=(T-t[2])/.35;if(f4>=0&&f4<1)o+=K.dot(g.bx+g.bw+8+(g.W-g.bx-g.bw-20)*f4,cy,5,C.amber,1-f4*.6);});
    /* loop lag: how long the oldest queued request has waited */
    var lag=s.q.length?(T-s.q[0][0])*1000:.3,hot=lag>50;
    o+=K.rich(cx,g.lag,[['이벤트 루프 지연(event loop lag): ',null,0],[(lag>=100?K.grp(lag):K.num(lag,1))+' ms',hot?C.redText:C.greenText,1]],{fs:13,a:'middle'});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){var s=state(T);return {queued:s.q.length,done:s.done};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
