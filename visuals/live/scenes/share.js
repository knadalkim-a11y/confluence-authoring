/* Scene kind "share": composition as 100% bars (one per row: e.g. last year, this year).
   One highlighted category is saturated, the rest light, so the claim's category stands out;
   without a highlight the categories get light tints. Inside labels only where they fit. */
CA_SCENES['share']=function(D,K,GR){
  var C=K.C,cats=D.categories,rows=D.rows,H=D.highlight;
  var TINT=['#a5d8ff','#d0bfff','#b2f2bb','#ffd8a8','#dee2e6','#ffc9c9'],GRAY=['#ced4da','#e9ecef','#dee2e6','#f1f3f5','#ced4da','#e9ecef'];
  function fill(j){return H<0?TINT[j]:j===H?C.blueText:GRAY[j];}
  function ink(j){return H>=0&&j===H?'#fff':C.ink;}   /* both pairs >= 4.5:1 */
  function pct(v){return Number(v).toFixed(D.decimals||0)+'%';}
  function geom(W){var g={W:W,nw:W<560},lw=0,x=0,y=12;rows.forEach(function(r){lw=Math.max(lw,K.tw(r.label,12));});
    g.lw=Math.min(W*0.25,lw+10);g.x0=g.lw+8;g.x1=W;g.leg=[];
    cats.forEach(function(c,j){var w=K.tw(c,11)+20;if(x+w>W){x=0;y+=18;}g.leg.push([x,y]);x+=w+6;});
    g.top=y+16;g.rh=g.nw?34:40;g.cy=g.top+rows.length*g.rh+16;g.H=g.top+rows.length*g.rh+(D.change?22:2);
    g.mark=D.labels.data_kind!=='측정값';if(g.mark)g.H+=16;return g;}
  function draw(T,g){var o=g.mark?K.text(g.W,g.H-3,D.labels.data_kind,{fs:11,c:C.muted,a:'end'}):'';
    cats.forEach(function(c,j){var p=g.leg[j];o+=K.rect(p[0],p[1]-9,10,10,{r:2,fill:fill(j),st:'#adb5bd',sw:.8})+K.text(p[0]+14,p[1],c,{fs:11,c:j===H?C.ink:C.muted,w:j===H?700:400});});
    rows.forEach(function(r,i){var y=g.top+i*g.rh,x=g.x0,bw=g.x1-g.x0;
      o+=K.text(g.lw,y+g.rh/2+3,r.label,{fs:12,c:C.text,a:'end'});
      r.pct.forEach(function(p,j){var w=bw*p/100;o+=K.rect(x,y+4,Math.max(0,w-1.5),g.rh-12,{r:2,fill:fill(j)});
        /* name + share where it fits, else the share alone; the table always has everything */
        var s=pct(p),n=cats[j]+' '+s;if(w>=K.tw(n,11)+10)s=n;if(w>=K.tw(s,11)+8)o+=K.text(x+w/2,y+g.rh/2+2,s,{fs:11,c:ink(j),a:'middle',w:j===H?700:400});x+=w;});});
    if(D.change)o+=K.text(g.W,g.cy,D.change,{fs:12,c:C.blueText,a:'end',w:700});
    return o;}
  function stats(){return {left:[]};}
  function probe(){return {};}
  return {end:1,geom:geom,draw:draw,stats:stats,probe:probe};
};
