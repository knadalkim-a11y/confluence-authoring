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
      g.cards=[0,1,2].map(function(j){return {x:g.sx,y:g.top+j*(g.ch+g.gap),w:g.sw,h:g.ch};});g.H=g.top+3*g.ch+2*g.gap+16;
      var lm=g.lb.y+g.lb.h/2,dm=g.db.y+g.db.h/2,t1=g.lb.w+26,t2=g.db.x-26;g.lb.y=g.cards[1].y+g.ch/2-g.lb.h/2;g.db.y=g.lb.y;lm=g.lb.y+g.lb.h/2;dm=lm;
      /* one trunk from the LB, square branches into each card; the same on the DB side */
      g.inp=g.cards.map(function(c){var cm=c.y+c.h/2;return [[g.lb.w,lm],[t1,lm],[t1,cm],[c.x,cm]];});
      g.out=g.cards.map(function(c){var cm=c.y+c.h/2;return [[c.x+c.w,cm],[t2,cm],[t2,dm],[g.db.x,dm]];});
      g.trunk=[[t1,g.cards[0].y+g.ch/2],[t1,g.cards[2].y+g.ch/2]];g.trunk2=[[t2,g.cards[0].y+g.ch/2],[t2,g.cards[2].y+g.ch/2]];}
    else{var sp=10,cx0=24,cx1=W-24;g.lb={x:cx0,y:26,w:150,h:48};g.ch=58;g.gap=12;g.top=g.lb.y+g.lb.h+22;
      g.cards=[0,1,2].map(function(j){return {x:cx0,y:g.top+j*(g.ch+g.gap),w:cx1-cx0,h:g.ch};});
      g.db={x:cx1-150,y:g.top+3*g.ch+2*g.gap+22,w:150,h:48};g.H=g.db.y+g.db.h+26;
      var lm=g.lb.y+g.lb.h/2,dm=g.db.y+g.db.h/2;
      /* phone: a spine down the left edge into each card, and up the right edge to the DB; no wire crosses a card */
      g.inp=g.cards.map(function(c){var cm=c.y+c.h/2;return [[cx0,lm],[sp,lm],[sp,cm],[cx0,cm]];});
      g.out=g.cards.map(function(c){var cm=c.y+c.h/2;return [[cx1,cm],[W-sp,cm],[W-sp,dm],[cx1,dm]];});
      g.trunk=[[sp,lm],[sp,g.cards[2].y+g.ch/2]];g.trunk2=[[W-sp,g.cards[0].y+g.ch/2],[W-sp,dm]];}
    return g;}
  function poly(pts,c,sw,d){return K.wire(pts,c,{sw:sw,d:d});}
  /* k-th of n tokens on a looping route at pace px/s; a new lap is a new token */
  function lap(pts,T,pace,k,n,id){var L=K.plen(pts),u=T*pace/L+k/n,a=K.at(pts,(u%1)*L);return [a.x,a.y,id+'-'+Math.floor(u)];}
  function draw(T,g){var o='',n=live(T),slow=T>=D.slow-1e-9,re=n<3,lb=g.lb,db=g.db;
    o+=K.rich(0,14,[['유입 트래픽: ',null,0],[re?'재분배 중':'균등 분배',re?C.redText:C.blueText,1]],{fs:13});
    o+=poly(g.trunk,C.edge,1.5)+poly(g.trunk2,slow?C.amberCell:C.edge,1.4);
    g.cards.forEach(function(c,j){var ok=alive(j,T),pi=g.inp[j],po=g.out[j],br=g.nw?pi.slice(2):pi.slice(1),bo=g.nw?po.slice(0,2):po.slice(0,2);
      o+=poly(j===1||g.nw?pi:br,ok?C.edge:C.faint,1.5,ok?null:'4 3');   /* the middle branch carries the LB stub */
      o+=poly(j===1||g.nw?po:bo,ok?(slow?C.amberCell:C.edge):C.rule,1.4,ok?null:'4 3');
      if(ok){for(var k=0;k<3;k++){var q=lap(pi,T+j*.4,K.M.speed,k,3,'i'+j+'.'+k);o+=K.token(q[0],q[1],q[2],3.5,C.blue,.9);}
        var q2=lap(po,(Math.min(T,D.slow)+Math.max(0,T-D.slow)*.3)+j*.7,K.M.speed,0,1,'o'+j);   /* the DB slows the return flow without a jump */o+=K.token(q2[0],q2[1],q2[2],3.5,slow?C.amber:C.blue,.9);
        if(!g.nw){var bx=(pi[2][0]+pi[3][0])/2;o+=K.text(bx,pi[3][1]-7,Math.round(100/n)+'%',{fs:12,c:C.blueText,a:'middle',w:700,halo:1});}}
      else{var xx=(pi[2][0]+pi[3][0])/2,yy=pi[3][1];o+=K.ring(xx,yy,8,'#fff',C.red,1.8)+K.line(xx-3.5,yy-3.5,xx+3.5,yy+3.5,C.red,{sw:1.8})+K.line(xx-3.5,yy+3.5,xx+3.5,yy-3.5,C.red,{sw:1.8});}});
    /* LB */
    o+=K.rect(lb.x,lb.y,lb.w,lb.h,{r:8,fill:C.blueSoft,st:C.blue,sw:1.6})+K.text(lb.x+lb.w/2,lb.y+lb.h/2-2,'LB',{fs:15,c:C.blueText,a:'middle',w:700})+K.text(lb.x+lb.w/2,lb.y+lb.h/2+15,'로드 밸런서',{fs:11,c:C.muted,a:'middle'});
    var hist=[3];D.fail.slice().filter(function(x){return x!=null&&T>=x;}).forEach(function(){hist.push(hist[hist.length-1]-1);});
    if(!g.nw){o+=K.text(lb.x+lb.w/2,lb.y+lb.h+20,'정상 서버',{fs:12,c:C.muted,a:'middle'});
      o+=K.rich(lb.x+lb.w/2,lb.y+lb.h+38,hist.map(function(v,k){return [(k?' → ':'')+v,k===hist.length-1?(v<3?C.redText:C.greenText):C.muted,k===hist.length-1?1:0];}),{fs:13,a:'middle'});}
    else o+=K.rich(lb.x+lb.w+10,lb.y+lb.h/2+5,[['정상 서버 ',null,0],[String(n),n<3?C.redText:C.greenText,1]],{fs:12});
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
