/* Scene kind "timeline": schedule bars per track with status colour, milestones, today line.
   Static: a schedule is read, not watched. Positions come from the spec (days or units). */
CA_SCENES['timeline']=function(D,K,GR){
  var C=K.C,T0=D.time.start,T1=D.time.stop,tr=D.tracks;
  /* [border, fill, label, text colour inside the bar]: inside-text pairs are >= 4.5:1 */
  var ST={done:[C.green,'#b2f2bb','완료',C.greenText],active:[C.blueText,C.blueText,'진행','#fff'],planned:[C.faint,'#fff','예정',C.muted],late:['#e03131','#e03131','지연','#fff'],risk:[C.amber,C.amber,'위험',C.ink]};
  function geom(W){var g={W:W,nw:W<560},lw=0;tr.forEach(function(t){lw=Math.max(lw,K.tw(t.label,12));});
    g.lw=Math.min(W*0.3,lw+10);g.x0=g.lw+10;g.x1=W-6;g.ms=D.milestones.length?2:0;g.top=22+g.ms*17;g.rh=g.nw?26:28;
    g.H=g.top+tr.length*g.rh+(D.today?20:0)+24;return g;}
  function X(g,v){return g.x0+(g.x1-g.x0)*(v-T0)/(T1-T0);}
  function draw(T,g){var o='',bottom=g.top+tr.length*g.rh;
    D.ticks.forEach(function(t){var x=X(g,t[0]),r=x>g.x1-28;o+=K.line(x,16,x,bottom,C.rule)+K.text(r?x-3:x+3,12,t[1],{fs:11,c:C.muted,a:r?'end':'start'});});
    D.milestones.forEach(function(m,i){var x=X(g,m[0]),y=22+(i%2)*17+8;o+=K.line(x,y,x,bottom,C.purple,{d:'2 3',op:.6});
      o+='<path d="M'+K.f(x)+' '+K.f(y-5)+'L'+K.f(x+5)+' '+K.f(y)+'L'+K.f(x)+' '+K.f(y+5)+'L'+K.f(x-5)+' '+K.f(y)+'Z" fill="'+C.purple+'"/>';
      o+=K.text(x>g.x1-90?x-8:x+8,y+4,m[1]+' '+m[2],{fs:11,c:C.purpleText,a:x>g.x1-90?'end':'start',w:700,halo:1});});
    tr.forEach(function(t,i){var y=g.top+i*g.rh,s=ST[t.status],x=X(g,t.a),w=X(g,t.b)-x;
      o+=K.text(g.lw,y+g.rh/2+4,t.label,{fs:12,c:C.text,a:'end'});
      o+=K.rect(x,y+6,w,g.rh-12,{r:4,fill:s[1],st:s[0],sw:1.3,d:t.status==='planned'?'4 3':null});
      /* note belongs to the bar's end: right of it when there is room, else inside its end */
      if(t.note){var nw=K.tw(t.note,11),xe=x+w;if(xe+6+nw<=g.x1)o+=K.text(xe+6,y+g.rh/2+4,t.note,{fs:11,c:t.status==='late'?C.redText:C.muted,w:700});
        else if(w>nw+10)o+=K.text(xe-5,y+g.rh/2+4,t.note,{fs:11,c:s[3],a:'end',w:700});}});
    if(D.today){var tx=X(g,D.today[0]);o+=K.line(tx,g.top-4,tx,bottom+4,C.ink,{sw:1.4})+K.text(tx,bottom+17,D.today[1],{fs:11,c:C.ink,a:tx>g.x1-40?'end':'middle',w:700,halo:1});}
    var used={},lx=g.x1,ly=g.H-6;tr.forEach(function(t){used[t.status]=1;});
    ['late','risk','planned','active','done'].forEach(function(k){if(!used[k])return;var w=K.tw(ST[k][2],11)+16;lx-=w;o+=K.rect(lx,ly-9,10,10,{r:2,fill:ST[k][1],st:ST[k][0],d:k==='planned'?'3 2':null})+K.text(lx+14,ly,ST[k][2],{fs:11,c:C.muted});lx-=6;});
    return o;}
  function stats(){return {left:[]};}
  function probe(){return {};}
  return {end:1,geom:geom,draw:draw,stats:stats,probe:probe};
};
