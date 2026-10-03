/* Scene kind "bars": categorical comparison, or before/after pairs with the change in %.
   Static by default (motion "play" grows the bars once). Values come from the spec. */
CA_SCENES['bars']=function(D,K,GR){
  var C=K.C,end=D.time.end,items=D.items,P=D.paired;
  /* values are >= 0 (validated); keep the author's precision and thousands separators */
  function fmt(v){var p=Number(v).toFixed(D.decimals||0).split('.');return K.grp(+p[0])+(p[1]?'.'+p[1]:'')+D.unit;}
  function geom(W){var g={W:W,nw:W<560},lw=0;items.forEach(function(it){lw=Math.max(lw,K.tw(it.label,12));});
    g.lw=Math.min(W*0.34,lw+10);g.x0=g.lw+8;g.x1=W-(P?96:70);g.top=(D.target||P)?26:4;g.rh=P?38:30;
    g.H=g.top+items.length*g.rh+(P?6:10);return g;}
  function X(g,v){return g.x0+(g.x1-g.x0)*Math.min(v,D.max)/D.max;}
  function draw(T,g){var o='',k=D.captions.length&&T<end?Math.max(0,Math.min(1,T/end)):1;
    if(P){o+=K.rect(g.x0,4,9,9,{r:2,fill:'#ced4da'})+K.text(g.x0+13,12,D.pair_labels[0],{fs:11,c:C.muted});
      var lx=g.x0+13+K.tw(D.pair_labels[0],11)+14;o+=K.rect(lx,4,9,9,{r:2,fill:C.blue})+K.text(lx+13,12,D.pair_labels[1],{fs:11,c:C.muted});}
    items.forEach(function(it,i){var y=g.top+i*g.rh,hl=D.highlight.indexOf(it.label)>=0;
      o+=K.text(g.lw,y+g.rh/2+4,it.label,{fs:12,c:hl?C.ink:C.text,a:'end',w:hl?700:400});
      if(!P){var w=X(g,it.value*k)-g.x0;o+=K.rect(g.x0,y+6,w,g.rh-12,{r:3,fill:hl?C.blue:C.blueMid});
        o+=K.text(g.x0+w+6,y+g.rh/2+4,fmt(it.value*k),{fs:12,c:hl?C.blueText:C.text,w:hl?700:400,halo:1});}
      else{var wb=X(g,it.before*k)-g.x0,wa=X(g,it.after*k)-g.x0,ch=it.before?(it.after-it.before)/it.before*100:0,flat=Math.abs(ch)<=D.flat_pct,good=!flat&&(D.better==='lower'?ch<0:ch>0);
        o+=K.rect(g.x0,y+5,wb,11,{r:2,fill:'#ced4da'})+K.text(g.x0+wb+5,y+14,fmt(it.before*k),{fs:11,c:C.muted,halo:1});
        o+=K.rect(g.x0,y+19,wa,13,{r:2,fill:hl||good?C.blue:C.blueMid})+K.text(g.x0+wa+5,y+30,fmt(it.after*k),{fs:12,c:C.blueText,w:700,halo:1});
        if(k>=1&&it.before)o+=K.text(g.W,y+g.rh/2+5,flat?'≈ 그대로':(ch>0?'+':'−')+Math.abs(ch).toFixed(Math.abs(ch)<1?1:0)+'%',{fs:13,c:flat?C.muted:good?C.greenText:C.redText,a:'end',w:700});}});
    if(D.target){var tx=X(g,D.target[0]);o+=K.line(tx,g.top-4,tx,g.top+items.length*g.rh,C.red,{d:'4 3',op:.8})+K.text(tx,g.top-8,D.target[1],{fs:11,c:C.redText,a:tx>g.x1-40?'end':'middle',w:700,halo:1});}
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {grow:Math.round(Math.min(1,T/end)*100)/100};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
