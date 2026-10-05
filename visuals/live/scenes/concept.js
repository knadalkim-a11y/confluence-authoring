/* Scene kind "concept": ideas, not numbers (visual_spec.concept_data). Three forms share the role tones
   (K.TONE) and the default choreography (scripts/choreo.py): each column / band / message enters in turn.
   compare  - 2-3 columns of role-coloured boxes, a dashed divider (and an optional arrow label) between them;
              stacked with horizontal dividers on phones.
   stack    - bands top to bottom, height by size, an optional side bracket and an empty "free" band above them.
   sequence - actors on top, dashed lifelines, numbered messages as arrows (dashed = reply). */
CA_SCENES['concept']=function(D,K,GR){
  var C=K.C,end=D.time.end,CH=CA_CHOREO(D.cues,K),F=D.form;
  function wrap(s,fs,w){var out=[],cur='';String(s).split(' ').forEach(function(wd){var c=cur?cur+' '+wd:wd;if(!cur||K.tw(c,fs)<=w)cur=c;else{out.push(cur);cur=wd;}});if(cur)out.push(cur);return out;}
  function attr(svg,a){return svg.replace(/<(text|rect) /,'<$1 '+a+' ');}
  function on(key,T){return CH.v(key,'on',T,1);}
  function larr(x,y,c){return '<path d="M'+K.f(x+6)+' '+K.f(y-4)+'L'+K.f(x)+' '+K.f(y)+'L'+K.f(x+6)+' '+K.f(y+4)+'" fill="none" stroke="'+c+'" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>';}   /* arrow head pointing left */
  /* a role-coloured box with a centred name (one or two lines) and an optional sub line */
  /* inline: name and sub on one line when the box is wide enough (stack bands) */
  function fitsInline(name,sub,w,fs){return sub&&K.tw(name,fs)+K.tw(sub,12)+48<w;}
  function box(id,x,y,w,h,tone,name,sub,o){o=o||{};var t=K.TONE[tone],fs=o.fs||14;
    if(o.inline&&fitsInline(name,sub,w,fs)){var rr=attr(K.rect(x,y,w,h,{r:o.r==null?8:o.r,fill:t[0],st:t[1],sw:1.2,d:o.d}),'data-solid="'+id+'"');
      return rr+attr(K.rich(x+w/2,y+h/2+fs*.36,[[name,C.ink,1],['   '+sub,C.text,0]],{fs:fs,a:'middle'}),'data-in="'+id+'"');}
    var ln=K.tw(name,fs)>w-16?wrap(name,fs-1,w-14):[name],f=ln.length>1?fs-1:fs;
    var lh=f+4,bh=ln.length*lh+(sub?17:0),y0=y+(h-bh)/2+f*.85,s=attr(K.rect(x,y,w,h,{r:o.r==null?8:o.r,fill:t[0],st:t[1],sw:1.2,d:o.d}),'data-solid="'+id+'"');
    ln.forEach(function(l,k){s+=attr(K.text(x+w/2,y0+k*lh,l,{fs:f,c:C.ink,a:'middle',w:700}),'data-in="'+id+'"');});
    if(sub)s+=attr(K.text(x+w/2,y0+(ln.length-1)*lh+17,sub,{fs:12,c:C.text,a:'middle'}),'data-in="'+id+'"');
    return s;}
  var LH=17;   /* label line height: haloed 12 px lines need 17 px or their outlines touch */
  function bh(name,sub,w,fs,pad){return (K.tw(name,fs||14)>w-16?2:1)*((fs||14)+4)+(sub?17:0)+(pad==null?18:pad);}

  function geom(W){var g={W:W,nw:W<560};
    if(F==='compare'){var n=D.columns.length,gap=D.arrow?Math.max(76,K.tw(D.arrow,12)+28):40;g.v=g.nw||gap>W*.22;   /* the gap fits the arrow label; too wide a gap stacks the columns */
      if(!g.v){var cw=(W-gap*(n-1))/n;g.cols=D.columns.map(function(c,i){var x=i*(cw+gap),y=26,its=[];
          c.items.forEach(function(it){var h=Math.max(44,bh(it.name,it.sub,cw));its.push({y:y,h:h});y+=h+10;});
          var nl=c.note?wrap(c.note,12,cw):[];return {x:x,w:cw,its:its,ny:y+6,nl:nl,bottom:y+(nl.length?nl.length*16+4:0)};});
        g.H=Math.max.apply(null,g.cols.map(function(c){return c.bottom;}))+22;
        g.divs=[];for(var i=1;i<n;i++)g.divs.push({x:i*(cw+gap)-gap/2,y0:4,y1:g.H-24});}
      else{var y=0,cw2=W,tot=0;g.cols=[];g.divs=[];D.columns.forEach(function(c){tot+=c.items.length;});
        var two=tot>6,iw=two?(W-8)/2:W;   /* many items on a phone: two boxes per row keep the height budget */
        D.columns.forEach(function(c,i){if(i){g.divs.push({y:y+8});y+=D.arrow?34:20;}
          var top=y,its=[];y+=24;var rowH=0;c.items.forEach(function(it,j){var h=Math.max(34,bh(it.name,it.sub,iw,13,10)),col=two?j%2:0;
            if(two&&col===0&&j)y+=rowH+6,rowH=0;its.push({y:y,h:h,x:col*(iw+8),w:iw});rowH=Math.max(rowH,h);if(!two)y+=h+6,rowH=0;});
          if(two)y+=rowH+6;   /* phones: tighter boxes keep two stacked columns in the height budget */
          var nl=c.note?wrap(c.note,12,cw2):[];g.cols.push({x:0,w:cw2,top:top,its:its,ny:y+4,nl:nl});y+=(nl.length?nl.length*16+4:0)+4;});
        g.H=y+20;}}
    else if(F==='stack'){var bw=D.bracket?(g.nw?64:96):0,x1=W-bw,su=(D.free?1:0),y=4;D.layers.forEach(function(l){su+=l.size;});
      var unit=g.nw?Math.max(28,Math.min(36,260/su)):Math.max(30,Math.min(42,300/su));g.x1=x1;g.bands=[];   /* bands share a fixed height budget; sizes stay proportional */
      if(D.free){g.free={y:y,h:unit};y+=unit+6;}
      D.layers.forEach(function(l){var fs=g.nw?13:14,need=fitsInline(l.name,l.sub,x1,fs)?fs+18:bh(l.name,l.sub,x1,fs)+2,h=Math.max(unit*l.size,need);g.bands.push({y:y,h:h});y+=h+6;});
      g.top=g.bands[0].y;g.bot=y-6;g.H=y+20;}
    else{var n2=D.actors.length,aw=Math.min(g.nw?84:150,(W-12*(n2-1))/n2),sp=(W-aw)/(n2-1);g.aw=aw;g.ax=D.actors.map(function(a,i){return aw/2+i*sp;});
      g.ah=g.nw?40:46;var y2=g.ah+18;g.rows=D.messages.map(function(m){var self=m.a===m.b,span=self?(g.nw?110:160):Math.abs(g.ax[m.b]-g.ax[m.a])-12,
          ln=wrap(m.mark+'\u00a0'+m.text,12,Math.max(60,span)),r={y:y2+ln.length*LH+4,ln:ln,self:self};y2=r.y+(self?26:14);return r;});
      g.H=y2+30;}
    return g;}

  function compare(T,g){var o='';
    g.divs.forEach(function(d,i){var u=on('d'+(i+1),T);
      if(!g.v){o+=K.enter(K.line(d.x,d.y0,d.x,d.y1,C.edge,{d:'4 4',sw:1.2})+(D.arrow?attr(K.text(d.x,g.H/2-14,D.arrow,{fs:12,c:C.text,a:'middle',w:700,plate:1}).replace(/<text /,'<text data-free="1" '),'')+K.line(d.x-14,g.H/2,d.x+12,g.H/2,C.faint,{sw:1.5})+K.arrow(d.x+14,g.H/2,C.faint):''),u,'d'+(i+1));}
      else o+=K.enter(K.line(0,d.y,g.W,d.y,C.edge,{d:'4 4',sw:1.2})+(D.arrow?K.text(g.W/2,d.y+20,'↓ '+D.arrow,{fs:12,c:C.text,a:'middle',w:700}):''),u,'d'+(i+1));});
    D.columns.forEach(function(c,i){var cg=g.cols[i],t=K.TONE[c.tone],hy=g.v?cg.top+16:16;
      o+=K.enter(K.text(cg.x+(g.v?0:cg.w/2),hy,c.label,{fs:14,c:t[2],a:g.v?'start':'middle',w:700}),on('h'+i,T),'h'+i);
      c.items.forEach(function(it,j){var b=cg.its[j];o+=K.enter(box('c'+i+'_'+j,cg.x+(b.x||0),b.y,b.w||cg.w,b.h,it.tone,it.name,it.sub,{fs:g.v?13:14}),on('c'+i+'.'+j,T),'c'+i+'.'+j,6);});
      cg.nl.forEach(function(l,k){o+=K.enter(K.text(cg.x+(g.v?0:cg.w/2),cg.ny+12+k*16,l,{fs:12,c:C.text,a:g.v?'start':'middle'}),on('h'+i,T),'n'+i+'.'+k);});});
    return o;}

  function stack(T,g){var o='';
    if(g.free)o+=K.rect(0,g.free.y,g.x1,g.free.h,{r:6,fill:'#fff',st:C.edge,d:'4 4'})+K.text(g.x1/2,g.free.y+g.free.h/2+4,D.free,{fs:12,c:C.muted,a:'middle'});
    D.layers.forEach(function(l,i){var b=g.bands[i];o+=K.enter(box('l'+i,0,b.y,g.x1,b.h,l.tone,l.name,l.sub,{fs:g.nw?13:14,r:6,inline:1}),on('l'+i,T),'l'+i,-8);});   /* bands settle from above */
    if(D.bracket){var bx=g.x1+10,u=on('br',T),y0=g.free?g.free.y:g.top,lb=wrap(D.bracket,12,(g.W-bx)-14);
      var s=K.line(bx,y0,bx,g.bot,C.faint,{sw:1.5})+K.line(bx-5,y0,bx,y0,C.faint,{sw:1.5})+K.line(bx-5,g.bot,bx,g.bot,C.faint,{sw:1.5});
      lb.forEach(function(l,k){s+=K.text(bx+8,(y0+g.bot)/2-(lb.length-1)*8+k*16+4,l,{fs:12,c:C.text,w:700});});
      o+=K.enter(s,u,'br');}
    return o;}

  function sequence(T,g){var o='',ah=g.ah,last=g.rows.length?g.rows[g.rows.length-1].y+20:ah+30;
    D.actors.forEach(function(a,i){var x=g.ax[i];o+=K.line(x,ah,x,g.H-22,C.edge,{d:'3 4',sw:1.2});
      o+=box('a'+i,x-g.aw/2,0,g.aw,ah,a.tone,a.name,'',{fs:g.nw?12:14});});
    D.messages.forEach(function(m,k){var r=g.rows[k],u=on('m'+k,T),xa=g.ax[m.a],xb=g.ax[m.b],c=m.dashed?C.muted:C.blue,s='';
      if(r.self){var w=g.nw?22:30;s+=K.wire([[xa,r.y-8],[xa+w,r.y-8],[xa+w,r.y+8],[xa+4,r.y+8]],c,{sw:1.5,d:m.dashed?'5 4':null})+larr(xa+2,r.y+8,c);
        r.ln.forEach(function(l,j){s+=K.text(xa+w+6,r.y-8+j*LH+4,l,{fs:12,c:C.text,w:j?400:700});});}
      else{var dir=xb>xa?1:-1,x1=xa+(xb-xa)*Math.max(.001,u);   /* the arrow is drawn from sender to receiver */
        s+=K.line(xa,r.y,x1-dir*2,r.y,c,{sw:1.6,d:m.dashed?'5 4':null});if(u>.98)s+=dir>0?K.arrow(xb-2,r.y,c):larr(xb+2,r.y,c);
        var cx=(xa+xb)/2;r.ln.forEach(function(l,j){s+=K.text(cx,r.y-6-(r.ln.length-1-j)*LH,l,{fs:12,c:m.dashed?C.text:C.blueText,a:'middle',w:j?400:700,halo:1});});}
      o+=K.enter(s,Math.min(1,u*1.5),'m'+k);});
    return o;}

  function draw(T,g){var o=F==='compare'?compare(T,g):F==='stack'?stack(T,g):sequence(T,g);
    return o+K.text(g.W,g.H-4,D.labels.data_kind,{fs:12,c:C.muted,a:'end'});}
  function stats(){return {left:[]};}
  function probe(T){return {};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
