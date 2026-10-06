/* Scene: timeout mismatch. User -> gateway (gives up at its timeout, returns 504) -> backend
   (finishes later, logs 200, its answer is dropped). Two dashboards below show what each layer
   records. Times and rates come from the Python model (monitoring_cases.timeout_model). */
CA_SCENES['timeout']=function(D,K,GR){
  var C=K.C;
  function geom(W){var g={W:W,nw:W<560},bw=g.nw?(W-24)/3:Math.min(160,(W-80)/3),bh=g.nw?64:76;g.bw=bw;g.bh=bh;
    g.xu=0;g.xg=(W-bw)/2;g.xb=W-bw;g.y=30;g.dy=g.y+bh+(g.nw?44:52);g.dh=g.nw?60:64;g.H=g.dy+g.dh+(g.nw?26:20);return g;}
  function draw(T,g){var o='',y=g.y,bh=g.bh,bw=g.bw,gwT=Math.min(T,D.gw),dead=T>=D.gw-1e-9,done=T>=D.be-1e-9,my=y+bh/2;
    o+=K.rich(0,14,[['경과 ',null,0],[K.num(Math.min(T,D.end_h||T),1)+'s',C.ink,1]],{fs:13});
    /* wires */
    o+=K.line(g.xu+bw,my,g.xg-2,my,C.edge,{sw:1.5})+K.arrow(g.xg-2,my,C.faint)+K.line(g.xg+bw,my,g.xb-2,my,done?C.redRail:C.edge,{sw:1.5,d:done?'4 3':null})+K.arrow(g.xb-2,my,C.faint);
    /* boxes */
    o+=K.rect(g.xu,y,bw,bh,{r:8,fill:C.paper2,st:C.edge,sw:1.2})+K.text(g.xu+bw/2,my+5,'사용자',{fs:g.nw?13:15,c:C.ink,a:'middle',w:700});
    o+=K.rect(g.xg,y,bw,bh,{r:8,fill:dead?C.redSoft:C.blueSoft,st:dead?C.red:C.blue,sw:1.6})+K.text(g.xg+bw/2,y+(g.nw?22:26),'게이트웨이',{fs:g.nw?13:15,c:dead?C.redText:C.blueText,a:'middle',w:700});
    o+=K.text(g.xg+bw/2,y+(g.nw?46:56),dead?'504 반환':K.num(gwT,1)+'s',{fs:g.nw?15:19,c:dead?C.redText:(gwT>D.gw*.8?C.redText:C.ink),a:'middle',w:700});
    o+=K.text(g.xg+bw/2,y+bh+18,'타임아웃 '+K.grp(D.gw)+'s',{fs:12,c:C.muted,a:'middle'});
    o+=K.rect(g.xb,y,bw,bh,{r:8,fill:'#fff',st:done?C.green:C.edge,sw:done?1.6:1.2})+K.text(g.xb+bw/2,y+(g.nw?22:26),'백엔드',{fs:g.nw?13:15,c:C.ink,a:'middle',w:700});
    if(done)o+=K.text(g.xb+bw/2,y+(g.nw?40:46),'완료',{fs:13,c:C.greenText,a:'middle',w:700});
    else o+=K.text(g.xb+bw/2,y+(g.nw?40:46),K.num(Math.min(T,D.be),1)+'s / '+K.grp(D.be)+'s',{fs:12,c:C.text,a:'middle',w:700});
    o+=K.rect(g.xb+12,y+bh-(g.nw?14:18),bw-24,7,{r:3,fill:C.rule})+K.rect(g.xb+12,y+bh-(g.nw?14:18),(bw-24)*K.clamp(T/D.be),7,{r:3,fill:done?C.green:C.blue});
    o+=K.text(g.xb+bw/2,y+bh+18,'처리 '+K.grp(D.be)+'s (슬로 쿼리)',{fs:12,c:C.muted,a:'middle'});
    /* request token: user -> gateway -> backend; a 504 goes back to the user */
    var t0=.35;if(T<t0){var f=T/t0;o+=K.token(g.xu+bw+(g.xg-g.xu-bw)*f,my,'req1',5,C.blue);}
    else if(T<t0*2){var f2=(T-t0)/t0;o+=K.token(g.xg+bw+(g.xb-g.xg-bw)*f2,my,'req2',5,C.blue);}
    if(dead){o+=K.pill(g.xu+bw/2,y+bh+18,'504 수신','hot',{fs:12});}
    if(done){var xm=(g.xg+bw+g.xb)/2;o+=K.ring(xm,my,9,'#fff',C.red,2)+K.line(xm-4,my-4,xm+4,my+4,C.red,{sw:2})+K.line(xm-4,my+4,xm+4,my-4,C.red,{sw:2});
      o+=K.text(xm,y-8,'응답 버려짐',{fs:12,c:C.redText,a:'middle',w:700,halo:1});}
    /* two dashboards */
    var dw=(g.W-(g.nw?10:60))/2,x2=dw+(g.nw?10:60),dy=g.dy,dh=g.dh;
    o+=K.rect(0,dy,dw,dh,{r:8,fill:dead?C.redSoft:C.paper2,st:dead?C.red:C.edge,sw:1.2})+K.text(dw/2,dy+20,'게이트웨이가 보는 세상',{fs:12,c:C.muted,a:'middle'});
    o+=K.text(dw/2,dy+dh-14,dead?'504 에러율 '+Math.round(D.gw_error)+'%':'504 에러율 —',{fs:g.nw?14:17,c:dead?C.redText:C.muted,a:'middle',w:700});
    o+=K.rect(x2,dy,dw,dh,{r:8,fill:done?C.greenSoft:C.paper2,st:done?C.green:C.edge,sw:1.2})+K.text(x2+dw/2,dy+20,'백엔드가 보는 세상',{fs:12,c:C.muted,a:'middle'});
    o+=K.text(x2+dw/2,dy+dh-14,done?'성공률 '+Math.round(D.be_success)+'%':'성공률 —',{fs:g.nw?14:17,c:done?C.greenText:C.muted,a:'middle',w:700});
    if(done&&!g.nw)o+=K.ring(g.W/2,dy+dh/2,12,C.amberSoft,C.amber,2)+K.text(g.W/2,dy+dh/2+5,'?',{fs:14,c:C.amberText,a:'middle',w:700});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {elapsed:Math.round(Math.min(T,D.end_h||T)*10)/10,gw504:T>=D.gw-1e-9?1:0,beDone:T>=D.be-1e-9?1:0};}
  return {end:D.end_h,geom:geom,draw:draw,stats:stats,probe:probe};
};
