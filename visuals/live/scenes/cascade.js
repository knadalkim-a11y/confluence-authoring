/* Scene: cascading failure behind a load balancer. Loads, saturation and removal times come from
   the Python model (monitoring_cases.cascade_live_model); this file draws the state at T:
   LB -> three servers (load bar, status) -> DB, shares on the LB wires, removed servers crossed out. */
CA_SCENES['cascade']=function(D,K,GR){
  var C=K.C,end=D.end_h,TS=D.ts;
  function idx(T){return Math.max(0,Math.min(TS.length-1,Math.round(T/(TS[1]-TS[0]))));}
  function load(j,T){var i=Math.min(TS.length-2,Math.floor(T/(TS[1]-TS[0]))),a=D.loads[i][j],b=D.loads[i+1][j];
    if(D.fail[j]!=null&&T>=D.fail[j])return 0;return a+(b-a)*K.clamp((T-TS[i])/(TS[i+1]-TS[i]));}
  function alive(j,T){return D.fail[j]==null||T<D.fail[j]-1e-9;}
  function live(T){return [0,1,2].filter(function(j){return alive(j,T);}).length;}
  function geom(W){var g={W:W,nw:W<560};
    if(!g.nw){g.lb={x:0,y:96,w:96,h:62};g.db={x:W-86,y:96,w:86,h:62};g.sx=g.lb.w+70;g.sw=W-g.sx-g.db.w-60;g.ch=64;g.gap=22;g.top=30;
      g.cards=[0,1,2].map(function(j){return {x:g.sx,y:g.top+j*(g.ch+g.gap),w:g.sw,h:g.ch};});g.H=g.top+3*g.ch+2*g.gap+16;}
    else{g.lb={x:(W-140)/2,y:26,w:140,h:50};g.ch=58;g.gap=12;g.top=g.lb.y+g.lb.h+40;
      g.cards=[0,1,2].map(function(j){return {x:0,y:g.top+j*(g.ch+g.gap),w:W,h:g.ch};});
      g.db={x:(W-140)/2,y:g.top+3*g.ch+2*g.gap+40,w:140,h:50};g.H=g.db.y+g.db.h+30;}
    return g;}
  function port(r,side){return side==='l'?[r.x,r.y+r.h/2]:side==='r'?[r.x+r.w,r.y+r.h/2]:side==='t'?[r.x+r.w/2,r.y]:[r.x+r.w/2,r.y+r.h];}
  function draw(T,g){var o='',n=live(T),slow=T>=D.slow-1e-9,re=n<3,lb=g.lb,db=g.db;
    o+=K.rich(0,14,[['유입 트래픽: ',null,0],[re?'재분배 중':'균등 분배',re?C.redText:C.blueText,1]],{fs:13});
    /* wires first, cards and boxes over them */
    g.cards.forEach(function(c,j){var a=port(lb,g.nw?'b':'r'),b=port(c,g.nw?'t':'l'),ok=alive(j,T);
      if(g.nw){b=[c.x+c.w*(j+1)/4,c.y];}
      o+=K.line(a[0],a[1],b[0],b[1],ok?C.edge:C.faint,{sw:1.5,d:ok?null:'4 3'});
      var d=port(c,g.nw?'b':'r'),e=port(db,g.nw?'t':'l');if(!g.nw)o+=K.line(d[0],d[1],e[0],e[1],ok?(slow?C.amberCell:C.edge):C.rule,{sw:1.4,d:ok?null:'4 3'});
      if(ok){var sp=g.nw?0:1;for(var k=0;k<3;k++){var f=((T*0.55+k/3+j*.13)%1);o+=K.dot(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,3.5,C.blue,.9);}
        if(!g.nw){var f2=((T*(slow?.18:.55)+j*.21)%1);o+=K.dot(d[0]+(e[0]-d[0])*f2,d[1]+(e[1]-d[1])*f2,3.5,slow?C.amber:C.blue,.9);}
        var mx=a[0]+(b[0]-a[0])*.5,my=a[1]+(b[1]-a[1])*.5;if(!g.nw)o+=K.text(mx,my-6,Math.round(100/n)+'%',{fs:12,c:C.blueText,a:'middle',w:700,halo:1});}
      else{var xx=a[0]+(b[0]-a[0])*.35,yy=a[1]+(b[1]-a[1])*.35;o+=K.ring(xx,yy,8,'#fff',C.red,1.8)+K.line(xx-3.5,yy-3.5,xx+3.5,yy+3.5,C.red,{sw:1.8})+K.line(xx-3.5,yy+3.5,xx+3.5,yy-3.5,C.red,{sw:1.8});}});
    if(g.nw){var dt=port(db,'t');g.cards.forEach(function(c,j){if(alive(j,T))o+=K.line(c.x+c.w*(j+1)/4,c.y+c.h,dt[0],dt[1],slow?C.amberCell:C.edge,{sw:1.2});});}
    /* LB */
    o+=K.rect(lb.x,lb.y,lb.w,lb.h,{r:8,fill:C.blueSoft,st:C.blue,sw:1.6})+K.text(lb.x+lb.w/2,lb.y+lb.h/2-2,'LB',{fs:15,c:C.blueText,a:'middle',w:700})+K.text(lb.x+lb.w/2,lb.y+lb.h/2+15,'로드 밸런서',{fs:11,c:C.muted,a:'middle'});
    var hist=[3];D.fail.slice().filter(function(x){return x!=null&&T>=x;}).forEach(function(){hist.push(hist[hist.length-1]-1);});
    if(!g.nw){o+=K.text(lb.x+lb.w/2,lb.y+lb.h+20,'정상 서버',{fs:12,c:C.muted,a:'middle'});
      o+=K.rich(lb.x+lb.w/2,lb.y+lb.h+38,hist.map(function(v,k){return [(k?' → ':'')+v,k===hist.length-1?(v<3?C.redText:C.greenText):C.muted,k===hist.length-1?1:0];}),{fs:13,a:'middle'});}
    else o+=K.rich(lb.x+lb.w+8,lb.y+lb.h/2+5,[['정상 ',null,0],[String(n),n<3?C.redText:C.greenText,1]],{fs:12});
    /* servers */
    g.cards.forEach(function(c,j){var ok=alive(j,T),L=load(j,T),hit=D.hit[j]!=null&&T>=D.hit[j]-1e-9,st=!ok?['제외',C.muted]:hit?['헬스체크 실패',C.redText]:L>=80?['포화 임박',C.amberText]:['정상',C.greenText];
      var col=!ok?C.faint:L>=100?C.red:L>=80?C.amber:C.green;
      o+=K.rect(c.x,c.y,c.w,c.h,{r:8,fill:!ok?C.paper2:hit?C.redSoft:'#fff',st:!ok?C.rule:hit?C.red:L>=80?C.amber:C.edge,sw:hit||(!ok)?1.4:1.2});
      o+=K.text(c.x+14,c.y+22,'서버 '+(j+1),{fs:14,c:ok?C.ink:C.muted,w:700})+K.text(c.x+c.w-14,c.y+22,st[0],{fs:12,c:st[1],a:'end',w:700});
      var bw=c.w-28-46;o+=K.rect(c.x+14,c.y+c.h-20,bw,8,{r:4,fill:C.rule})+(ok?K.rect(c.x+14,c.y+c.h-20,bw*Math.min(1,L/100),8,{r:4,fill:col}):'');
      o+=K.text(c.x+c.w-14,c.y+c.h-12,ok?Math.round(L)+'%':'—',{fs:12,c:ok?(L>=100?C.redText:L>=80?C.amberText:C.text):C.muted,a:'end',w:700});});
    /* DB */
    o+=K.rect(db.x,db.y,db.w,db.h,{r:8,fill:slow?C.redSoft:'#fff',st:slow?C.red:C.green,sw:1.6})+K.text(db.x+db.w/2,db.y+db.h/2-2,'DB',{fs:15,c:C.ink,a:'middle',w:700});
    o+=K.text(db.x+db.w/2,db.y+db.h/2+16,slow?'2,000ms':'20ms',{fs:13,c:slow?C.redText:C.greenText,a:'middle',w:700});
    if(slow)o+=K.text(db.x+db.w/2,db.y-8,'슬로 쿼리',{fs:12,c:C.redText,a:'middle',w:700,halo:1});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {healthy:live(T)};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
