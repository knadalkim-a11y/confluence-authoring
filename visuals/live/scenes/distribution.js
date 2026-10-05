/* Scene kind "distribution": one dot per observation, stacked at its value, samples side by
   side (stacked on phones). The dots arrive first; then mean and percentile lines appear one at
   a time; an optional tail band says what share of requests sits in it. Statistics come from
   the Python model (visual_spec.distribution_data); this file only places them. */
CA_SCENES['distribution']=function(D,K,GR){
  var C=K.C,G=D.groups,end=D.time.end,TD=D.time.dots;
  var PAL={blue:[C.blue,C.blueText],green:[C.green,C.greenText],amber:[C.amber,C.amberText],red:[C.red,C.redText]};
  function num(v){return Math.abs(v-Math.round(v))<1e-9?K.grp(v):Number(v).toFixed(1);}
  function order(g){var o=[],mx=Math.max.apply(null,g.counts);for(var s=0;s<mx;s++)g.values.forEach(function(v,i){if(s<g.counts[i])o.push([i,s]);});return o;}
  function shown(g,T){return Math.min(g.stats.n,Math.floor(g.stats.n*Math.min(1,T/TD)+1e-9));}
  function geom(W){var g={W:W,nw:W<560,cols:[]},per=g.nw?1:G.length,cw=(W-24*(per-1))/per,y=0,ph=g.nw?78:150,rh=g.nw?16:18;g.rh=rh;
    G.forEach(function(gr,i){var x0=g.nw?0:i*(cw+24),top=g.nw?y:0,c={x0:x0,x1:x0+cw,top:top,lab:top+(g.nw?36:40),base:top+(g.nw?36:40)+rh*Math.min(4,D.markers.length)+ph};
      c.px0=x0+8;c.px1=x0+cw-8;c.X=function(v){return c.px0+(c.px1-c.px0)*v/D.max;};
      var mx=Math.max.apply(null,gr.counts),room=c.base-(c.lab+rh*Math.min(4,D.markers.length))-4;c.r=Math.min(4,Math.max(2,(c.px1-c.px0)/D.max*2));
      c.step=Math.min(c.r*2+1,room/mx);c.bottom=c.base+26;g.cols.push(c);y=c.bottom+(g.nw?8:16);});
    g.H=Math.max.apply(null,g.cols.map(function(c){return c.bottom;}))+(D.labels.data_kind!=='측정값'?18:2);return g;}
  function draw(T,g){var o='';
    G.forEach(function(gr,i){var c=g.cols[i],seq=order(gr),k=shown(gr,T),rows=[],tailOn=D.tail&&T>=D.tail.t-1e-9&&D.tail.shares[gr.label]>0;
      o+=K.text(c.x0,c.top+16,gr.label,{fs:15,c:C.ink,w:700})+K.text(c.x1,c.top+16,'요청 '+K.grp(gr.stats.n)+'건 · 세로: 요청 수',{fs:11,c:C.muted,a:'end'});
      if(tailOn){var tx=c.X(D.tail.at),fo=K.clamp((T-D.tail.t)/.6);o+=K.rect(tx,c.lab+4,c.px1-tx,c.base-c.lab-4,{r:2,fill:C.redSoft,op:fo});}   /* fades in, no frame */
      o+=K.line(c.px0,c.base,c.px1,c.base,C.edge,{sw:1.2});
      [0,D.max/2,D.max].forEach(function(v,j){o+=K.text(c.X(v),c.base+18,num(v)+(j===2?D.unit:''),{fs:11,c:C.muted,a:j===0?'start':j===2?'end':'middle'});});
      /* each dot drops from the top onto its stack (gravity: slow start, fast landing) */
      seq.slice(0,k).forEach(function(d,ix){var v=gr.values[d[0]],hot=tailOn&&v>=D.tail.at,y1=c.base-c.r-1-d[1]*c.step,t0=ix/gr.stats.n*TD,y0=c.lab-6,f=K.clamp((T-t0)/Math.max(.45,(y1-y0)/K.M.speed));   /* peak speed 2x the shared pace */
        o+=K.token(c.X(v),y0+(y1-y0)*f*f,'g'+i+'.'+ix,c.r,hot?C.red:C.blue,.35+.65*Math.min(1,f*3));});
      D.markers.forEach(function(m){if(T<m[3]-1e-9)return;var v=gr.stats[m[0]],x=c.X(v),s=m[1]+' '+num(v)+D.unit,w=K.tw(s,12),right=x+4+w>c.px1,x0=right?x-4-w:x+4,r=0;
        while(rows[r]&&rows[r].some(function(q){return x0<q[1]+6&&x0+w>q[0]-6;}))r++;(rows[r]=rows[r]||[]).push([x0,x0+w]);var ly=c.lab+r*g.rh;
        var gr2=K.clamp((T-m[3])/.5),e=1-(1-gr2)*(1-gr2);   /* the line is drawn downwards, then the label fades in */
        o+=K.line(x,ly+4,x,ly+4+(c.base-ly-4)*e,PAL[m[2]][0],{d:'4 3',sw:1.5});
        o+=K.text(right?x-4:x+4,ly,s,{fs:12,c:PAL[m[2]][1],a:right?'end':'start',w:700,halo:1}).replace('<text ','<text opacity="'+K.f(Math.min(1,.15+e))+'" ');});
      if(tailOn){var lb=D.tail.labels[gr.label],tx2=c.X(D.tail.at),mid=(tx2+c.px1)/2,lw=K.tw(lb,13);
        o+=K.text(Math.min(c.px1-lw/2-2,Math.max(tx2+lw/2+2,mid)),(c.lab+c.base)/2+18,lb,{fs:13,c:C.redText,a:'middle',w:700,halo:1});}});
    if(D.labels.data_kind!=='측정값')o+=K.text(g.W,g.H-3,D.labels.data_kind,{fs:12,c:C.muted,a:'end'});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {shown:G.map(function(gr){return shown(gr,T);})};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
