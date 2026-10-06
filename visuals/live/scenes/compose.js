/* Scene kind "compose" (visual_spec.compose_data; docs/design/motion-concept-architecture.md, section 12).
   A figure is a tree of layout containers and parts; every part works inside every container:
     containers  row | column | grid | stack | split | lifelines, each optionally framed (solid group or dashed
                 boundary) and annotated (label, note, banner, span arrow, side bracket, row separators);
     elements    box | pill | cylinder | doc, in a state (normal, selected, muted, error, ok), with a sub line,
                 a code fragment, a badge chip and a speech bubble;
     links       between any two elements, routed orthogonally from the laid-out boxes (straight when the boxes
                 face each other, one elbow otherwise, around the side with via), styles flow/reply/hidden/fail.
   Layout is measured, not fixed: rows give elements their natural width and containers the rest, gaps grow to
   fit link labels, and a row that does not fit folds into a column (phones). Each part registers what the shared
   gates check: data-solid/data-in (text stays in its box), data-k (no one-frame colour switch), data-wire +
   data-ends (no diagonal, no line through another box), data-frame (boxes and frames nest, never half overlap).
   Timing comes from Python cues: on (enter), act (state index), reveal (a link or message being drawn). */
CA_SCENES['compose']=function(D,K,GR){
  var C=K.C,end=D.time.end,CH=CA_CHOREO(D.cues,K),R=D.tree,LK=D.links||[];
  var MONO='ui-monospace,SFMono-Regular,Menlo,Consolas,monospace',LH=17;
  var EL={},UNDER={},NEL=0,PAR={},NS=0;
  (function idx(n){if(n.t==='e'){EL[n.id]=n;NEL++;return [n.id];}if(n.L==='stack')NS++;var ids=[];n.kids.forEach(function(k){PAR[k.id]=n;ids=ids.concat(idx(k));});
    var s={};ids.forEach(function(i){s[i]=1;});UNDER[n.id]=s;return ids;})(R);
  function under(n,id){return n.t==='e'?n.id===id:!!UNDER[n.id][id];}
  function wrap(s,fs,w){var out=[],cur='';String(s).split(' ').forEach(function(wd){var c=cur?cur+' '+wd:wd;if(!cur||K.tw(c,fs)<=w)cur=c;else{out.push(cur);cur=wd;}});if(cur)out.push(cur);return out;}
  function attr(svg,a){return svg.replace(/<(text|rect|polyline) /,'<$1 '+a+' ');}
  function on(key,T){return CH.v(key,'on',T,1);}
  /* layout decisions in plain words, for the build report (the author sees why, instead of guessing) */
  function note(g,t){if(g.notes.indexOf(t)<0)g.notes.push(t);}
  function cname(n){return (n.label?'"'+n.label+'" ':'')+'('+n.id+')';}
  /* content box: the union of the elements inside a container - labels and numbers attach to what is there, not to
     the container's full share of the row */
  function cbox(n,g){var x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(var id in UNDER[n.id]){var b=g.B[id];if(!b)continue;x0=Math.min(x0,b.x);y0=Math.min(y0,b.by!=null?b.by:b.y);x1=Math.max(x1,b.x+b.w);y1=Math.max(y1,b.y+b.h);}
    return x0>x1?null:{x:x0,y:y0,w:x1-x0,h:y1-y0};}
  function labelPos(n,g){var b=g.B[n.id],fy=b.y+b.top;if(n.frame)return {x:b.x+b.pl,y:fy+20};var c=cbox(n,g);return {x:c?Math.max(b.x,c.x):b.x,y:fy+15};}
  /* step numbers (D.marks): each captioned step's number sits on the part it points at */
  var MK={};(D.marks||[]).forEach(function(m,i){m.i=i;(MK[m.target]=MK[m.target]||[]).push(m);});
  function mkText(id){return (MK[id]||[]).map(function(m){return m.mark;}).join('');}
  function sum(a){return a.reduce(function(x,y){return x+y;},0);}
  function max(a){return a.length?Math.max.apply(null,a):0;}

  /* ---- element look by state; a state change mixes the two looks (cue "act") ---- */
  function sty(e,s){var t=K.TONE[e.tone];
    if(s==='selected')return {fill:t[0],st:t[2],sw:2.2,c:t[2],sc:C.text,w:700};
    if(s==='muted')return {fill:'#ffffff',st:C.edge,sw:1.2,c:C.muted,sc:C.muted,w:400};
    if(s==='error')return {fill:K.TONE.red[0],st:'#e03131',sw:2,c:K.TONE.red[2],sc:C.text,w:700};
    if(s==='ok')return {fill:K.TONE.green[0],st:'#2f9e44',sw:2,c:K.TONE.green[2],sc:C.text,w:700};
    return {fill:t[0],st:t[1],sw:1.2,c:C.ink,sc:C.text,w:700};}
  function styAt(e,T){var v=CH.v(e.id,'act',T,0),k=Math.min(Math.floor(v),e.sts.length-1),u=v-k,a=sty(e,e.sts[k]),o=a;
    if(u>1e-6&&k+1<e.sts.length){var b=sty(e,e.sts[k+1]);
      o={fill:K.mix(a.fill,b.fill,u),st:K.mix(a.st,b.st,u),sw:a.sw+(b.sw-a.sw)*u,c:K.mix(a.c,b.c,u),sc:K.mix(a.sc,b.sc,u),w:u<.5?a.w:b.w};}
    /* on the current step's path (cue "level"): the selected look, plus a short pop when the step starts */
    var h=CH.v(e.id,'level',T,0),pu=CH.v(e.id,'pop',T,0),t=K.TONE[e.tone];
    if(h>1e-6)o={fill:o.fill,st:K.mix(o.st,t[2],h),sw:o.sw+(2.2-o.sw)*h,c:K.mix(o.c,t[2],h),sc:o.sc,w:o.w};
    if(pu>0&&pu<1)o.sw+=.6*Math.sin(Math.PI*pu);
    return o;}
  /* the chip for the current state: a state change swaps it (old out, then new in) */
  function badgeAt(e,T){var v=CH.v(e.id,'act',T,0),k=Math.min(Math.floor(v),e.bds.length-1),u=v-k;
    if(u<=1e-6||k+1>=e.bds.length||JSON.stringify(e.bds[k])===JSON.stringify(e.bds[k+1]))return {b:e.bds[k],o:1};
    return u<.5?{b:e.bds[k],o:1-2*u}:{b:e.bds[k+1],o:2*u-1};}
  function anyBadge(e){return e.bds.filter(Boolean);}

  /* ---- measuring ---- */
  function word(s,fs){return max(String(s).split(' ').map(function(x){return K.tw(x,fs);}));}
  function eMin(e,g){var nm=Math.min(K.tw(e.name,g.fs),170)+28,sb=e.sub?Math.min(K.tw(e.sub,12),200)+24:0,cd=0;
    e.code.forEach(function(l){cd=Math.max(cd,K.tw(l,11)+36);});
    return Math.max(76,nm,sb,cd,max(anyBadge(e).map(function(b){return K.tw(b.text,11)+40;})),e.bubble?Math.min(K.tw(e.bubble,12)+24,120):0);}
  function eBody(e,w,g){var fs=g.fs,ln=K.tw(e.name,fs)>w-16?wrap(e.name,fs-1,w-14):[e.name],f=ln.length>1?fs-1:fs;
    var sub=!e.sub?[]:K.tw(e.sub,12)<=w-14?[e.sub]:wrap(e.sub,12,w-14);
    var ls=ln.length>1?f+6:f+4;   /* wrapped name lines need the extra 2 px or their boxes touch */
    var ch=ln.length*ls+sub.length*16+(anyBadge(e).length?24:0)+(e.code.length?e.code.length*15+14:0)+(e.bar!=null?12:0);
    return {ln:ln,f:f,ls:ls,sub:sub,ch:ch,h:Math.max(e.shape==='pill'?(38):(44),ch+(18)+(e.shape==='cylinder'?10:0))};}
  /* one rule set, read on monitors (715 px columns and narrower Confluence layouts); a too-narrow width folds rows
     into columns like any other lack of room, there are no phone-only rules */
  function bubble(e,w,g){if(!e.bubble)return null;var bw=Math.min(Math.max(w,K.tw(e.bubble,12)+24),w+48),ln=wrap(e.bubble,12,bw-18);
    bw=Math.max(Math.min(bw,max(ln.map(function(l){return K.tw(l,12);}))+24),60);return {w:bw,ln:ln,h:ln.length*16+10};}
  function minW(n,g){if(n.t==='e')return eMin(n,g);var p=padLR(n,g),m;
    if(n.L==='row')m=sum(n.kids.map(function(k){return minW(k,g);}))+sum(gaps(n,g));
    else if(n.L==='split')m=max(n.kids.map(function(k){return minW(k,g);}));
    else if(n.L==='lifelines')m=n.kids.length*(96);
    else if(n.L==='stack')m=150;
    else m=max(n.kids.map(function(k){return minW(k,g);}));
    return m+p;}
  function padLR(n,g){return (n.frame?(28):0)+(n.bracket?(96):0);}
  /* gaps between row neighbours: room for the labels of links that join them, and for a boundary separator */
  /* tight: a label may wrap at its spaces, so the gap only needs its longest word (rows try this before wrapping) */
  function gaps(n,g,tight){var out=[];for(var i=0;i+1<n.kids.length;i++){var a=n.kids[i],b=n.kids[i+1],gp=28,cnt=0;
      LK.forEach(function(l){if(l.via)return;if((under(a,l.a)&&under(b,l.b))||(under(a,l.b)&&under(b,l.a))){if(l.label)cnt++;
        gp=Math.max(gp,!l.label?44:tight?Math.max(44,max(l.label.split(' ').map(function(x){return K.tw(x,12);}))+28):Math.min(K.tw(l.label,12)+36,96));}});
      if(n.sep)gp=Math.max(gp,48);out.push(gp);}return out;}
  function vgap(n,i,g){var a=n.kids[i],b=n.kids[i+1],gp=12;
    LK.forEach(function(l){if(l.via)return;if((under(a,l.a)&&under(b,l.b))||(under(a,l.b)&&under(b,l.a)))gp=Math.max(gp,l.label?36:28);});
    if(n.sep)gp=Math.max(gp,30);return gp;}

  /* ---- layout: lay(node, x, y, w, g, stretchTo) places the subtree and returns its height ---- */
  function lay(n,x,y,w,g,minH){if(n.t==='e')return layEl(n,x,y,w,g,minH);
    var fr=n.frame,top=(n.span?30:0),lab=n.label&&!g.inSplit[n.id];
    var pl=fr?(14):0,pr=pl+(n.bracket?(96):0),pt=top+(fr?(n.label?32:14):(lab?24:0));
    var iw=w-pl-pr,ix=x+pl,iy=y+pt;
    var nl=n.note?wrap(n.note,12,iw):[],pb=(fr?12:0)+(n.banner?36:0)+(nl.length?nl.length*16+8:0);
    var b={x:x,y:y,w:w,top:top,pl:pl,pr:pr,pt:pt,pb:pb,nl:nl,fb:fr?12:0};g.B[n.id]=b;
    var h=n.L==='row'||(n.L==='column'&&g.rot[n.id])?layRow(n,ix,iy,iw,g):n.L==='grid'?layGrid(n,ix,iy,iw,g):n.L==='stack'?layStack(n,ix,iy,iw,g):
      n.L==='split'?laySplit(n,ix,iy,iw,g):n.L==='lifelines'?layLife(n,ix,iy,iw,g):layCol(n,ix,iy,iw,g,false);
    b=g.B[n.id]=Object.assign(g.B[n.id]||{},b);b.cy0=iy;b.cy1=iy+h;b.h=Math.max(pt+h+pb,minH||0);
    return b.h;}
  function layEl(e,x,y,w,g,minH){var bd=eBody(e,w,g),bu=bubble(e,w,g),ex=bu?bu.h+10:0,h=Math.max(bd.h,(minH||0)-ex,g.minh[e.id]||0);
    g.B[e.id]={x:x,y:y+ex,w:w,h:h,bd:bd,bu:bu,by:y};return ex+h;}
  function prefW(k,g,w){return k.t==='e'?Math.min(w,Math.max(minW(k,g)+24,128)*(k.grow||1)):null;}
  /* a row lays its items on one line; when they do not fit it wraps into lines of equal count (like text), and
     only when even two a line do not fit it folds into a column */
  function layRow(n,x,y,w,g){var ks=n.kids,gp=gaps(n,g),mins=ks.map(function(k){return minW(k,g);}),per=0;
    function fits(i0,i1){return sum(mins.slice(i0,i1))+sum(gp.slice(i0,i1-1))<=w;}
    if(!fits(0,ks.length)){var gt=gaps(n,g,1);if(sum(mins)+sum(gt)<=w)gp=gt;}   /* narrower gaps (labels wrap) before a second line */
    for(var L=1;L<=Math.ceil(ks.length/2)&&!per;L++){var c=Math.ceil(ks.length/L),ok=true;   /* fewest lines, items spread evenly over them */
      for(var i=0;i<ks.length;i+=c)if(!fits(i,Math.min(ks.length,i+c)))ok=false;if(ok)per=c;}
    if(!per){note(g,'row '+cname(n)+': '+ks.length+' items need '+Math.round(sum(mins)+sum(gp))+' px, '+Math.round(w)+' px available: folded into a column');return layCol(n,x,y,w,g,true);}
    if(per<ks.length)note(g,'row '+cname(n)+': '+ks.length+' items need '+Math.round(sum(mins)+sum(gp))+' px, '+Math.round(w)+' px available: wrapped into '+Math.ceil(ks.length/per)+' lines');
    var b=g.B[n.id]||(g.B[n.id]={}),cy=y,seps=[],hseps=[];
    var flip=false;
    for(var i0=0;i0<ks.length;i0+=per){var i1=Math.min(ks.length,i0+per),lk=ks.slice(i0,i1),lg=gp.slice(i0,i1-1),lm=mins.slice(i0,i1);
      /* a chain continues where the last line ended: when a link joins the end of one line to the start of the next,
         the next line runs the other way (snake order), so the link drops straight down instead of crossing back */
      if(i0&&LK.some(function(l){return !l.via&&((under(ks[i0-1],l.a)&&under(ks[i0],l.b))||(under(ks[i0-1],l.b)&&under(ks[i0],l.a)));}))flip=!flip;
      if(flip){lk=lk.slice().reverse();lg=lg.slice().reverse();lm=lm.slice().reverse();}
      var r=layLine(n,lk,lg,lm,x,cy,w,g);
      if(!r){note(g,'row '+cname(n)+': a container would get less than its minimum width: folded into a column');return layCol(n,x,y,w,g,true);}
      seps=seps.concat(r.seps);cy+=r.H;
      if(i1<ks.length){var vg=Math.max(28,gp[i1-1]>44?40:28);if(n.sep)hseps.push({y:cy+vg/2,x0:x,x1:x+w});cy+=vg;}}
    b=g.B[n.id]||(g.B[n.id]={});b.seps=n.sep?seps:[];b.hseps=hseps;
    return cy-y+(n.sep&&seps.length?28:0);}
  function layLine(n,ks,gp,mins,x,y,w,g){var ws=ks.map(function(k){return prefW(k,g,w);}),flex=[],fixed=0;
    ks.forEach(function(k,i){if(ws[i]==null)flex.push(i);else fixed+=ws[i];});
    var room=w-sum(gp);
    if(flex.length){var gw=sum(flex.map(function(i){return ks[i].grow||1;})),rest=room-fixed;
      flex.forEach(function(i){ws[i]=rest*(ks[i].grow||1)/gw;});
      var lack=sum(flex.map(function(i){return Math.max(0,mins[i]-ws[i]);}));
      if(lack>0){var spare=sum(ks.map(function(k,i){return ws[i]!=null&&k.t==='e'?ws[i]-mins[i]:0;}));
        if(spare<lack)return null;   /* containers share equally; one that would be squeezed folds the row instead */
        ks.forEach(function(k,i){if(k.t==='e')ws[i]-=(ws[i]-mins[i])*lack/spare;});
        rest=room-sum(ks.map(function(k,i){return k.t==='e'?ws[i]:0;}));flex.forEach(function(i){ws[i]=rest*(ks[i].grow||1)/gw;});}}
    else if(fixed>room){var sp=fixed-sum(mins);ks.forEach(function(k,i){ws[i]-=(ws[i]-mins[i])*(fixed-room)/sp;});}
    var extra=room-sum(ws),gx=gp.slice();
    if(extra>0&&gp.length){var add=Math.min(extra/gp.length,96);gx=gp.map(function(v){return v+add;});extra-=add*gp.length;}
    var hs=ks.map(function(k,i){return lay(k,0,0,ws[i],g);}),H=max(hs),cx=x+Math.max(0,extra)/2,seps=[];
    ks.forEach(function(k,i){var framed=k.t==='c'&&k.frame;lay(k,cx,framed?y:y+(H-hs[i])/2,ws[i],g,framed?H:0);
      if(i<gx.length)seps.push({x:cx+ws[i]+gx[i]/2,y0:y,y1:y+H});cx+=ws[i]+(gx[i]||0);});
    return {H:H,seps:seps};}
  /* a column of plain rows with the same number of items is a table: every row uses the same column widths and
     gaps (the widest cell of each column, the widest gap between two columns), so boxes with the same role line up
     and one row cannot decide differently from the others; containers in a column share the room left over */
  function plainRow(k){return k.t==='c'&&k.L==='row'&&!k.frame&&!k.label&&!k.span&&!k.note&&!k.banner&&!k.bracket;}
  function layTable(n,x,y,w,g){var rows=n.kids,c=rows[0].kids.length,i,r;
    var mins=[],ws=[],gp=[],flex=[];for(i=0;i<c;i++){mins.push(0);ws.push(0);flex.push(false);}for(i=0;i+1<c;i++)gp.push(0);
    rows.forEach(function(row){var gg=gaps(row,g);row.kids.forEach(function(k,i){mins[i]=Math.max(mins[i],minW(k,g));
        if(k.t==='e')ws[i]=Math.max(ws[i],prefW(k,g,w));else flex[i]=true;});gg.forEach(function(v,i){gp[i]=Math.max(gp[i],v);});});
    if(sum(mins)+sum(gp)>w){note(g,'column '+cname(n)+': its rows did not fit as a table ('+Math.round(sum(mins)+sum(gp))+' px needed, '+Math.round(w)+' px), laid row by row');return null;}
    ws=ws.map(function(v,i){return Math.max(v,mins[i]);});
    var room=w-sum(gp),fixed=sum(ws.map(function(v,i){return flex[i]?0:v;})),nf=flex.filter(Boolean).length;
    if(nf){var rest=room-fixed;flex.forEach(function(f,i){if(f)ws[i]=Math.max(mins[i],rest/nf);});}
    if(sum(ws)>room){var sp=sum(ws)-sum(mins);ws=ws.map(function(v,i){return v-(v-mins[i])*(sum(ws)-room)/Math.max(1,sp);});}
    var extra=room-sum(ws);if(extra>0&&gp.length){var add=Math.min(extra/gp.length,96);gp=gp.map(function(v){return v+add;});extra-=add*gp.length;}
    var x0=x+Math.max(0,extra)/2,xs=[],cx=x0;ws.forEach(function(v,i){xs.push(cx);cx+=v+(gp[i]||0);});
    var cy=y;rows.forEach(function(row,ri){var hs=row.kids.map(function(k,i){return lay(k,0,0,ws[i],g);}),H=max(hs);
      row.kids.forEach(function(k,i){var framed=k.t==='c'&&k.frame;lay(k,xs[i],framed?cy:cy+(H-hs[i])/2,ws[i],g,framed?H:0);});
      g.B[row.id]={x:x0,y:cy,w:cx-x0,h:H,top:0,pl:0,pr:0,pt:0,pb:0,nl:[],fb:0,cy0:cy,cy1:cy+H,hseps:[],
        seps:row.sep?gp.map(function(v,i){return {x:xs[i]+ws[i]+v/2,y0:cy,y1:cy+H};}):[]};
      cy+=H+(row.sep?28:0);if(ri+1<rows.length)cy+=vgap(n,ri,g);});
    note(g,'column '+cname(n)+': '+rows.length+' rows aligned as a table of '+c+' columns');
    var b=g.B[n.id]||(g.B[n.id]={});b.seps=[];b.hseps=[];return cy-y;}
  function layCol(n,x,y,w,g,folded){var ks=n.kids,cy=y,hseps=[];
    if(!folded&&ks.length>=2&&ks.every(plainRow)&&ks[0].kids.length>=2&&ks.every(function(k){return k.kids.length===ks[0].kids.length;})){var th=layTable(n,x,y,w,g);if(th!=null)return th;}
    var fill=g.fill[n.id];
    ks.forEach(function(k,i){var kw=k.t==='e'&&!fill?Math.min(w,Math.max(minW(k,g)+48,240)):w,h=lay(k,x+(w-kw)/2,cy,kw,g);cy+=h;
      if(i+1<ks.length){var gp=vgap(n,i,g);if(folded&&n.sep)hseps.push(cy+gp/2);cy+=gp;}});
    var b=g.B[n.id]||(g.B[n.id]={});b.seps=[];b.hseps=hseps.map(function(sy){return {y:sy,x0:x,x1:x+w};});
    return cy-y;}
  function layGrid(n,x,y,w,g){var c=n.cols,gp=12,mx=max(n.kids.map(function(k){return minW(k,g);}));
    while(c>1&&(w-(c-1)*gp)/c<mx)c--;var cw=(w-(c-1)*gp)/c,cy=y;
    for(var r=0;r<n.kids.length;r+=c){var row=n.kids.slice(r,r+c),hs=row.map(function(k){return lay(k,0,0,cw,g);}),H=max(hs);
      row.forEach(function(k,j){lay(k,x+j*(cw+gp),cy,cw,g,H);});cy+=H+gp;}
    var b=g.B[n.id]||(g.B[n.id]={});b.seps=[];b.hseps=[];return cy-gp-y;}
  function inline(e,w,g){return !e.code.length&&!anyBadge(e).length&&e.bar==null&&(!e.sub||K.tw(e.name,g.fs)+K.tw(e.sub,12)+48<w)&&K.tw(e.name,g.fs)+24<w;}   /* one line in a band: name (and sub) */
  function layStack(n,x,y,w,g){var su=(n.free?1:0)+sum(n.kids.map(function(k){return k.size;})),cy=y,
      unit=Math.max(30,Math.min(42,300/su)),b=g.B[n.id]||(g.B[n.id]={});   /* bands share a height budget; sizes stay proportional */
    b.free=null;if(n.free){b.free={x:x,y:cy,w:w,h:unit};cy+=unit+6;}
    n.kids.forEach(function(k){var il=inline(k,w,g),need=il?g.fs+(18):eBody(k,w,g).h,h=Math.max(unit*k.size,need);layEl(k,x,cy,w,g,h);g.B[k.id].il=il;g.B[k.id].h=h;cy+=h+6;});   /* the band is exactly its slot: need already fits its text */
    b.seps=[];b.hseps=[];return cy-6-y;}
  function laySplit(n,x,y,w,g){var k=n.kids.length,gp=n.arrow?Math.max(76,K.tw(n.arrow,12)+28):40,b=g.B[n.id]||(g.B[n.id]={}),
      v=gp>w*.22||sum(n.kids.map(function(p){return minW(p,g);}))+gp*(k-1)>w;   /* the gap fits the arrow label; too wide a gap stacks the sides */
    b.v=v;b.hdr=[];b.divs=[];b.seps=[];b.hseps=[];if(v)note(g,'split '+cname(n)+': sides stacked (side by side needs '+Math.round(sum(n.kids.map(function(p){return minW(p,g);}))+gp*(k-1))+' px, '+Math.round(w)+' px available)');
    if(!v){var tot=w-gp*(k-1),mins=n.kids.map(function(p){return minW(p,g);}),ws=n.kids.map(function(){return tot/k;});
      for(var it=0;it<k;it++){var big=n.kids.map(function(p,i){return mins[i]>ws[i]+.5;}),nb=big.filter(Boolean).length;if(!nb)break;   /* a side that needs more room gets its minimum; the others share the rest */
        var left=tot-sum(mins.filter(function(m,i){return big[i]||ws[i]<0;}));ws=ws.map(function(x0,i){return big[i]?mins[i]:left/(k-nb);});}
      var hs=n.kids.map(function(p,i){return lay(p,0,0,ws[i],g);}),H=max(hs),px=x;
      n.kids.forEach(function(p,i){lay(p,px,y+26,ws[i],g,p.frame?H:0);var cb=cbox(p,g);if(p.label&&!p.frame)b.hdr.push({x:cb?cb.x+cb.w/2:px+ws[i]/2,y:y+16,a:'middle',p:p});
        if(i)b.divs.push({x:px-gp/2,y0:y+4,y1:y+26+H});px+=ws[i]+gp;});
      b.my=y+26+H/2;return H+26+4;}
    var cy=y;n.kids.forEach(function(p,i){if(i){b.divs.push({y:cy+8,x0:x,x1:x+w});cy+=n.arrow?34:20;}
      var hh=null;if(p.label&&!p.frame){hh={x:x,y:cy+16,a:'start',p:p};b.hdr.push(hh);cy+=24;}cy+=lay(p,x,cy,w,g)+4;if(hh){var cb=cbox(p,g);if(cb)hh.x=cb.x;}});
    return cy-y;}
  function layLife(n,x,y,w,g){var k=n.kids.length,aw=Math.min(150,(w-12*(k-1))/k),sp=(w-aw)/(k-1),ah=46,b=g.B[n.id]||(g.B[n.id]={});
    b.ax=n.kids.map(function(a,i){return x+aw/2+i*sp;});b.ah=ah;b.seps=[];b.hseps=[];
    n.kids.forEach(function(a,i){g.B[a.id]={x:b.ax[i]-aw/2,y:y,w:aw,h:ah,bd:eBody(a,aw,g),bu:null,by:y,actor:1};});
    var y2=y+ah+18;b.rows=n.msgs.map(function(m){var self=m.a===m.b,span=self?(160):Math.abs(b.ax[m.b]-b.ax[m.a])-12,
        ln=wrap((m.mark?m.mark+' ':'')+m.text,12,Math.max(60,span)),r={y:y2+ln.length*LH+4,ln:ln,self:self};y2=r.y+(self?26:14);return r;});
    return y2-y;}

  function geom(W){var g={W:W,B:{},inSplit:{},fill:{},rot:{},minh:{},notes:[]};g.fs=14;
    (function mark(n){if(n.t==='e')return;if(n.L==='split')n.kids.forEach(function(p){g.inSplit[p.id]=1;g.fill[p.id]=1;});n.kids.forEach(mark);})(R);
    function gut(side){var m=0;LK.forEach(function(l){if(l.via===side)m=Math.max(m,18+(l.label?K.tw(l.label,12)+8:0));});return m;}
    var vl=gut('left'),vr=gut('right'),ml=vl||2,mr=vr||2,top=4,h=lay(R,ml,top,W-ml-mr,g);
    if((D.marks||[]).some(function(m){var b=g.B[m.target];return m.kind==='e'&&b&&b.y<12||m.kind==='c'&&b&&b.y<12;})){g.B={};top=14;h=lay(R,ml,top,W-ml-mr,g)+top-4;}   /* a number on a top-row part needs room above it */   /* 2 px keeps box borders off the edge */g.routes=routes(g);
    g.fh=h;var y=h+4;g.sl=[];
    note(g,'height '+Math.round(h)+' px for the figure; top-level parts: '+R.kids.map(function(k){var b=g.B[k.id];return (k.t==='e'?k.name:cname(k))+' '+Math.round(b.h+(b.by!=null?b.y-b.by:0))+' px';}).join(', '));
    if((D.slist||[]).length){y+=10;D.slist.forEach(function(it){var ln=wrap(it.text,13,W-48);g.sl.push({y:y+13,ln:ln});y+=ln.length*LH+(3);});}
    g.lg=[];var dk=K.tw(D.labels.data_kind,12)+16,lx=2,rows=[[]];
    (D.legend||[]).forEach(function(d){var w=24+K.tw(d.text,12)+14;if(lx+w>W-dk&&rows[rows.length-1].length){rows.push([]);lx=2;}rows[rows.length-1].push({d:d,x:lx});lx+=w;});
    if((D.legend||[]).length){y+=6;rows.forEach(function(r,i){r.forEach(function(it){it.y=y+(i+1)*20-4;g.lg.push(it);});});y+=(rows.length-1)*20;}   /* the last legend row shares the line of the data-kind label */
    g.H=y+26;g.lab=labels(g);return g;}

  /* ---- links: orthogonal routes from the laid-out boxes ---- */
  /* plan: which sides a link leaves and enters; straight when the boxes face each other, one elbow otherwise */
  /* axis: how the two ends are arranged where their branches meet - the children of their lowest common container
     that hold them; stacked branches join vertically, side-by-side ones horizontally (a tree drops, a chain runs) */
  function axis(l,g){var up={},n=EL[l.a];while(n){up[n.id]=n;n=PAR[n.id];}var cb=EL[l.b],ca;
    while(cb&&!up[PAR[cb.id]&&PAR[cb.id].id])cb=PAR[cb.id];if(!cb||!PAR[cb.id])return null;var lca=PAR[cb.id];
    ca=EL[l.a];while(ca&&PAR[ca.id]!==lca)ca=PAR[ca.id];if(!ca)return null;var A=g.B[ca.id],B2=g.B[cb.id];
    if(A.y+A.h<=B2.y+1||B2.y+B2.h<=A.y+1)return {ax:'v',at:A.y<B2.y?(A.y+A.h+B2.y)/2:(B2.y+B2.h+A.y)/2};
    if(A.x+A.w<=B2.x+1||B2.x+B2.w<=A.x+1)return {ax:'h',at:A.x<B2.x?(A.x+A.w+B2.x)/2:(B2.x+B2.w+A.x)/2};return null;}
  function plan(l,g){var a=g.B[l.a],b=g.B[l.b];
    if(l.via)return {m:'via'};
    var ax=axis(l,g);   /* elbows turn in the gap between the two branches (a bus between a parent and its row of children) */
    if(ax&&ax.ax==='v'&&(b.y>=a.y+a.h+4||b.y+b.h<=a.y-4)){var Dn0=b.y>=a.y+a.h,l0=Math.max(a.x,b.x)+8,h0=Math.min(a.x+a.w,b.x+b.w)-8;
      return {m:h0>=l0?'vs':'v',sa:Dn0?'b':'t',sb:Dn0?'t':'b',lo:l0,hi:h0,at:ax.at};}
    if(b.x>=a.x+a.w+4||b.x+b.w<=a.x-4){var Rt=b.x>=a.x+a.w,lo=Math.max(a.y,b.y)+8,hi=Math.min(a.y+a.h,b.y+b.h)-8;
      return {m:hi>=lo?'hs':'h',sa:Rt?'r':'l',sb:Rt?'l':'r',lo:lo,hi:hi,at:ax&&ax.ax==='h'?ax.at:null};}
    if(b.y>=a.y+a.h+4||b.y+b.h<=a.y-4){var Dn=b.y>=a.y+a.h,lo2=Math.max(a.x,b.x)+8,hi2=Math.min(a.x+a.w,b.x+b.w)-8;
      return {m:hi2>=lo2?'vs':'v',sa:Dn?'b':'t',sb:Dn?'t':'b',lo:lo2,hi:hi2,at:ax&&ax.ax==='v'?ax.at:null};}
    return null;}
  /* routes for all links: links that leave one side of a box share its centre, so a parent and its children form
     a trunk and a bus (the elbow sits in the gap between the branches); two-way pairs run as parallel lines */
  /* routes for all links: links that leave one side of a box share its centre, so a parent and its children form
     a trunk and a bus (the elbow sits in the gap between the branches); two-way pairs run as parallel lines.
     (v0.17 spread ports along busy sides and moved bends; measured with scripts/figure_metrics.py it added 43% more
     bends at 715 px and crossings on phones, so it was taken out again.) */
  function routes(g){var P=LK.map(function(l){return plan(l,g);});
    function cen(id){var b=g.B[id];return [b.x+b.w/2,b.y+b.h/2];}
    var EB=Object.keys(EL).map(function(id){return [id,g.B[id]];});
    function hit(pts,l){for(var i=1;i<pts.length;i++){var x0=Math.min(pts[i-1][0],pts[i][0]),x1=Math.max(pts[i-1][0],pts[i][0]),y0=Math.min(pts[i-1][1],pts[i][1]),y1=Math.max(pts[i-1][1],pts[i][1]);
        for(var j=0;j<EB.length;j++){var id=EB[j][0],b=EB[j][1];if(id===l.a||id===l.b)continue;if(x1>b.x+1&&x0<b.x+b.w-1&&y1>b.y+1&&y0<b.y+b.h-1)return true;}}return false;}
    /* around: leave the side of a, run outside every box in between, enter the same side of b */
    function around(l,side){var a=g.B[l.a],b=g.B[l.b],ya=a.y+a.h/2,yb=b.y+b.h/2,lo=Math.min(a.y,b.y),hi=Math.max(a.y+a.h,b.y+b.h),Lf=side==='left',X=Lf?Math.min(a.x,b.x):Math.max(a.x+a.w,b.x+b.w);
      EB.forEach(function(e){var c=e[1];if(c.y<hi&&c.y+c.h>lo)X=Lf?Math.min(X,c.x):Math.max(X,c.x+c.w);});X+=Lf?-12:12;
      if(X<2||X>g.W-2)return null;return [[Lf?a.x:a.x+a.w,ya],[X,ya],[X,yb],[Lf?b.x:b.x+b.w,yb]];}
    g.side={};
    return LK.map(function(l,k){var r=route1(l,k);if(l.via){g.side[k]=l.via;return r;}if(r&&hit(r,l)){var al=[around(l,'right'),around(l,'left')];
        for(var i=0;i<2;i++)if(al[i]&&!hit(al[i],l)){g.side[k]=i?'left':'right';note(g,'link '+l.id+': the direct path crosses a box, routed around the '+g.side[k]);return al[i];}
        g.blocked=1;note(g,'link '+l.id+': no clear path (direct or around a side); reorder the items or add via');}return r;});
    function route1(l,k){var p=P[k];if(!p)return null;var a=g.B[l.a],b=g.B[l.b],ac=cen(l.a),bc=cen(l.b),
        twin=LK.some(function(o){return o!==l&&o.a===l.b&&o.b===l.a&&!o.via;}),off=twin?(LK.some(function(o,j){return j<k&&o.a===l.b&&o.b===l.a;})?7:-7):0;   /* the earlier link of a pair runs above (left), its label above it */
      function pick(lo,hi,c1,c2){var m=(lo+hi)/2;return c1>=lo&&c1<=hi?c1:c2>=lo&&c2<=hi?c2:m;}
      function sx(bx,sd){return sd==='r'?bx.x+bx.w:bx.x;}function sy(bx,sd){return sd==='b'?bx.y+bx.h:bx.y;}
      if(p.m==='via')return around(l,l.via);
      if(p.m==='hs'){var yy=Math.max(p.lo,Math.min(p.hi,pick(p.lo,p.hi,ac[1],bc[1])+off));return [[sx(a,p.sa),yy],[sx(b,p.sb),yy]];}
      if(p.m==='vs'){var xx=Math.max(p.lo,Math.min(p.hi,pick(p.lo,p.hi,ac[0],bc[0])+off));return [[xx,sy(a,p.sa)],[xx,sy(b,p.sb)]];}
      if(p.m==='h')return K.ortho([[sx(a,p.sa),ac[1]+off],[sx(b,p.sb),bc[1]+off]],'h',p.at);
      return K.ortho([[ac[0]+off,sy(a,p.sa)],[bc[0]+off,sy(b,p.sb)]],'v',p.at);}}
  /* label places, decided once per layout: candidates on every segment (longest first) - above/below a run,
     right/left of a drop - and the first that clears every box, earlier labels and the figure edge wins. The later
     link of a two-way pair tries below first; a loop around the side labels its outer side first. */
  function labels(g){var taken=Object.keys(EL).map(function(id){var b=g.B[id];return [b.x,b.y,b.x+b.w,b.y+b.h];});
    (function cl(n){if(n.t==='e')return;var b=g.B[n.id];   /* group names, split headers and separator words are taken too */
      if(n.label&&!g.inSplit[n.id]){var lp=labelPos(n,g),x0=lp.x,y0=lp.y;taken.push([x0-2,y0-13,x0+K.tw(n.label,13)+(mkText(n.id)?26:4),y0+4]);}
      (b.hdr||[]).forEach(function(h){var w=K.tw(h.p.label,14)+4,x0=h.a==='middle'?h.x-w/2:h.x;taken.push([x0,h.y-14,x0+w,h.y+4]);});
      (b.seps||[]).forEach(function(sp){var w=K.tw(n.sep,12)+4;taken.push([sp.x-w/2,sp.y1+11,sp.x+w/2,sp.y1+28]);});
      n.kids.forEach(cl);})(R);
    function free(r){if(r[0]<2||r[2]>g.W-2||r[1]<0||r[3]>g.fh+2)return false;for(var i=0;i<taken.length;i++){var q=taken[i];if(r[2]>q[0]+1&&r[0]<q[2]-1&&r[3]>q[1]+1&&r[1]<q[3]-1)return false;}return true;}
    return LK.map(function(l,k){var p=g.routes[k];if(!p)return null;var out={},below=LK.some(function(o,j){return j<k&&o.a===l.b&&o.b===l.a&&!o.via;}),sd=g.side[k],
        first=!below&&LK.some(function(o){return o!==l&&o.a===l.b&&o.b===l.a&&!o.via;});   /* of a two-way pair, each label sits on its line's outer side */
      var segs=[];for(var i=1;i<p.length;i++)segs.push(i);segs.sort(function(x,y){return Math.hypot(p[y][0]-p[y-1][0],p[y][1]-p[y-1][1])-Math.hypot(p[x][0]-p[x-1][0],p[x][1]-p[x-1][1]);});
      var a0=p[segs[0]-1],b0=p[segs[0]],mx0=(a0[0]+b0[0])/2,my0=(a0[1]+b0[1])/2;
      if(l.style==='fail'){out.x=mx0;out.y=my0+5;taken.push([mx0-9,my0-9,mx0+9,my0+8]);}
      var lt=(mkText(l.id)?mkText(l.id)+(l.label?' ':''):'')+(l.label||'');
      if(!lt)return out;
      var cands=[];segs.forEach(function(i){var a=p[i-1],b=p[i],hz=Math.abs(a[1]-b[1])<.5,mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2,len=Math.hypot(b[0]-a[0],b[1]-a[1]);
        if(hz){var ln=K.tw(lt,12)>len-12?wrap(lt,12,Math.max(40,len-12)):[lt],up={lx:mx,ly:my-6-(ln.length-1)*LH,an:'middle',ln:ln},dn={lx:mx,ly:my+16,an:'middle',ln:ln};
          if(l.style==='fail'){up.ly-=11;dn.ly+=13;}cands.push.apply(cands,below?[dn,up]:[up,dn]);}
        else[.5,.3,.7,.15,.85].forEach(function(f){var yy=a[1]+(b[1]-a[1])*f+4,r={lx:mx+6,ly:yy,an:'start',ln:[lt]},lf={lx:mx-6,ly:yy,an:'end',ln:[lt]};   /* along a drop: middle first, then nearer either end */
          cands.push.apply(cands,sd==='left'||(!sd&&first)?[lf,r]:[r,lf]);});});
      function box(c){var w=max(c.ln.map(function(x){return K.tw(x,12);}))+4,x0=c.an==='start'?c.lx-2:c.an==='end'?c.lx-w+2:c.lx-w/2;return [x0,c.ly-13,x0+w,c.ly+(c.ln.length-1)*LH+4];}
      var pick=null;for(var j=0;j<cands.length&&!pick;j++)if(free(box(cands[j])))pick=cands[j];
      if(!pick){var best=1e9;cands.forEach(function(c){var r=box(c),a=0;taken.forEach(function(q){a+=Math.max(0,Math.min(r[2],q[2])-Math.max(r[0],q[0]))*Math.max(0,Math.min(r[3],q[3])-Math.max(r[1],q[1]));});
          if(r[0]<2||r[2]>g.W-2)a+=1e6;if(a<best){best=a;pick=c;}});}   /* nowhere free: the least covered place (the gates report it) */taken.push(box(pick));out.lx=pick.lx;out.ly=pick.ly;out.an=pick.an;out.ln=pick.ln;return out;});}
  var LS={none:{c:C.faint,t:C.muted,d:'2 4'},flow:{c:C.blue,t:C.blueText,d:null},reply:{c:'#868e96',t:C.text,d:'5 4'},hidden:{c:C.red,t:C.redText,d:'3 3'},fail:{c:C.red,t:C.redText,d:null}};
  function trim(p,len){var o=[p[0]],d=0;for(var i=1;i<p.length;i++){var s=Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]);
      if(d+s>=len){var r=s?(len-d)/s:0;o.push([p[i-1][0]+(p[i][0]-p[i-1][0])*r,p[i-1][1]+(p[i][1]-p[i-1][1])*r]);return o;}o.push(p[i]);d+=s;}return o;}
  function head(p,c){var n=p.length,x=p[n-1][0],y=p[n-1][1],dx=x-p[n-2][0],dy=y-p[n-2][1],l=Math.hypot(dx,dy)||1,ux=dx/l,uy=dy/l,bx=x-7*ux,by=y-7*uy;
    return '<path data-head="1" d="M'+K.f(bx-4*uy)+' '+K.f(by+4*ux)+'L'+K.f(x)+' '+K.f(y)+'L'+K.f(bx+4*uy)+' '+K.f(by-4*ux)+'" fill="none" stroke="'+c+'" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>';}
  function longest(p){var bi=1,bl=-1;for(var i=1;i<p.length;i++){var l=Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]);if(l>bl){bl=l;bi=i;}}return bi;}
  var HOT={none:'#868e96',flow:'#1864ab',reply:'#495057',hidden:'#c92a2a',fail:'#c92a2a'};
  function link(l,k,T,g){var p=g.routes[k];if(!p)return '';var u=CH.v(l.id,'reveal',T,1);if(u<=0)return '';
    var s=LS[l.style],h=CH.v(l.id,'level',T,0),c=K.mix(s.c,HOT[l.style],h),L=K.plen(p),q=u<1?trim(p,L*u):p,   /* on the current step's path: darker and wider */
      o=attr(K.wire(q,c,{sw:1.6+1.2*h,d:s.d}),'data-ends="'+l.a+' '+l.b+'"');
    if(u>=.999&&l.style!=='none')o+=head(p,c);
    var lv=K.clamp((u-.5)/.5),t='',P=g.lab[k];
    if(P&&P.x!=null)t+=K.text(P.x,P.y,'✕',{fs:14,c:C.redText,a:'middle',w:700,plate:1}).replace(/<text /,'<text data-free="1" ');
    if(P&&P.ln)P.ln.forEach(function(x,j){t+=K.text(P.lx,P.ly+j*LH,x,{fs:12,c:s.t,a:P.an,w:700,plate:1}).replace(/<text /,'<text data-free="1" '+(j===0&&mkText(l.id)?'data-mark="'+mkText(l.id)+'" ':''));});
    if(t)o+=K.enter(t,lv,l.id+'.t');
    return o;}
  function token(l,k,T,g){var p=g.routes[k];if(!p||!l.token)return '';var s0=CH.since(l.id,'reveal',T);if(s0==null)return '';
    var t1=s0+K.wall(D.rate,s0,.5),L=K.plen(p),dur=K.wall(D.rate,t1,L/K.M.speed);   /* one dot at the shared pace (K.M.speed px per second on screen) */
    if(T<t1||T>=t1+dur||t1+dur>end)return '';var q=K.at(p,(T-t1)/dur*L);return K.token(q.x,q.y,l.id+'.k',4,LS[l.style].c);}

  /* a step that follows a path sends one dot along its links (through each box on the way), at least at the kit
     pace and fast enough to arrive within the step (capped well under the gate's speed limit) */
  function pathTokens(T,g){var o='';(D.paths||[]).forEach(function(P,k){var ts=P.t0+K.wall(D.rate,P.t0,.3);if(T<ts||T>=P.t1)return;
      P.routes.forEach(function(r,j){var pts=[];r.forEach(function(lid){var i=-1;LK.forEach(function(l,ii){if(l.id===lid)i=ii;});var q=g.routes[i];if(!q)return;
          if(pts.length){var bb=g.B[LK[i].a];pts.push([bb.x+bb.w/2,bb.y+bb.h/2]);}pts=pts.concat(q);});
        if(pts.length<2)return;var L=K.plen(pts),rt=K.wall(D.rate,ts,1),avail=(P.t1-ts)/rt,v=Math.min(300,Math.max(K.M.speed,L/(avail*.85))),dur=K.wall(D.rate,ts,L/v);
        if(T>=ts+dur)return;var q=K.at(pts,(T-ts)/dur*L);o+=K.token(q.x,q.y,'p'+k+'_'+j,4.5,C.blue);});});return o;}
  function stepList(T,g){var o='';(g.sl||[]).forEach(function(it,k){var lv=CH.v('sl'+k,'level',T,1),c=lv<=1?K.mix(C.muted,C.text,lv):K.mix(C.text,C.blueText,lv-1);
      it.ln.forEach(function(x,j){o+=attr(K.text(14,it.y+j*LH,(j?'':D.slist[k].mark+' ')+x,{fs:13,c:c,w:lv>1.5?700:400}),j?'':'data-k="sl'+k+'"');});});return o;}
  function legend(g){var o='';(g.lg||[]).forEach(function(it){var x=it.x,y=it.y;
      if(it.d.style)o+=K.line(x,y-4,x+18,y-4,LS[it.d.style].c,{sw:1.6,d:LS[it.d.style].d});
      else{var t=K.TONE[it.d.tone||'gray'];o+=K.rect(x+2,y-11,14,12,{r:it.d.shape==='pill'?6:3,fill:t[0],st:t[1],d:it.d.dashed?'3 2':null});}
      o+=K.text(x+24,y,it.d.text,{fs:12,c:C.text});});return o;}

  /* ---- drawing ---- */
  function shape(e,b,s){var o={r:e.shape==='pill'?Math.min(b.h/2,22):e.shape==='doc'?4:e.shape==='cylinder'?6:8,fill:s.fill,st:s.st,sw:s.sw,d:e.dashed?'5 3':null},
      r=attr(K.rect(b.x,b.y,b.w,b.h,o),'data-solid="'+e.id+'" data-k="'+e.id+'.s"');
    if(e.shape==='cylinder')r+='<path d="M'+K.f(b.x)+' '+K.f(b.y+8)+'Q'+K.f(b.x+b.w/2)+' '+K.f(b.y+20)+' '+K.f(b.x+b.w)+' '+K.f(b.y+8)+'" fill="none" stroke="'+s.st+'" stroke-width="'+K.f(s.sw)+'"/>';
    if(e.shape==='doc')r+='<path d="M'+K.f(b.x+b.w-12)+' '+K.f(b.y)+'L'+K.f(b.x+b.w)+' '+K.f(b.y+12)+'" fill="none" stroke="'+s.st+'" stroke-width="'+K.f(s.sw)+'"/>';
    return r;}
  function element(e,T,g){var b=g.B[e.id],s=styAt(e,T),bd=b.bd,cx=b.x+b.w/2,o=shape(e,b,s),din='data-in="'+e.id+'"';
    if(b.il){o+=attr(K.rich(cx,b.y+b.h/2+g.fs*.36,[[e.name,s.c,s.w===700?1:0]].concat(e.sub?[['   '+e.sub,s.sc,0]]:[]),{fs:g.fs,a:'middle'}),din);}
    else{var y=b.y+(b.h-bd.ch)/2+(e.shape==='cylinder'?5:0)+bd.f*.85;
      bd.ln.forEach(function(l){o+=attr(K.text(cx,y,l,{fs:bd.f,c:s.c,a:'middle',w:s.w}),din);y+=bd.ls;});
      bd.sub.forEach(function(l){o+=attr(K.text(cx,y,l,{fs:12,c:s.sc,a:'middle'}),din);y+=16;});
      if(anyBadge(e).length){var ba=badgeAt(e,T);if(ba.b)o+=K.enter(K.pill(cx,y+6,ba.b.text,ba.b.kind,{fs:11}).replace(/<text /,'<text '+din+' '),ba.o,e.id+'.b'+(ba.b.text));y+=24;}
      if(e.code.length){var cy=y-8;o+=K.rect(b.x+10,cy,b.w-20,e.code.length*15+8,{r:4,fill:'#fff',st:C.rule});
        e.code.forEach(function(l,j){o+=attr('<text x="'+K.f(b.x+18)+'" y="'+K.f(cy+15+j*15)+'" font-size="11" font-family="'+MONO+'" fill="'+C.ink+'" xml:space="preserve">'+K.esc(l)+'</text>',din);});y+=e.code.length*15+14;}
      if(e.bar!=null){var bw=b.w-24,by0=b.y+b.h-12;o+=K.rect(b.x+12,by0,bw,4,{r:2,fill:C.rule})+K.rect(b.x+12,by0,Math.max(2,bw*e.bar),4,{r:2,fill:K.TONE[e.tone][1]});}}   /* a relative amount, not a measurement */
    if(b.bu){var bu=b.bu,bx=Math.max(0,Math.min(g.W-bu.w,cx-bu.w/2)),by=b.by,t=K.TONE[e.tone];
      o+=K.rect(bx,by,bu.w,bu.h,{r:8,fill:'#fff',st:t[1],sw:1.2})+'<path d="M'+K.f(cx-6)+' '+K.f(by+bu.h-.5)+'L'+K.f(cx)+' '+K.f(by+bu.h+7)+'L'+K.f(cx+6)+' '+K.f(by+bu.h-.5)+'" fill="#fff" stroke="'+t[1]+'" stroke-width="1.2"/>';
      bu.ln.forEach(function(l,j){o+=K.text(bx+bu.w/2,by+17+j*16,l,{fs:12,c:C.text,a:'middle'});});}
    return K.enter(o,on(e.id,T),e.id,6);}
  function container(n,T,g){var b=g.B[n.id],t=K.TONE[n.tone],o='',fy=b.y+b.top,lab=n.label&&!g.inSplit[n.id];
    if(n.span){o+=K.text(b.x+b.w/2,b.y+12,n.span,{fs:12,c:C.text,a:'middle',w:700});
      o+=K.line(b.x+4,b.y+22,b.x+b.w-6,b.y+22,C.faint,{sw:1.5})+K.arrow(b.x+b.w-4,b.y+22,C.faint)+K.line(b.x+4,b.y+17,b.x+4,b.y+27,C.faint,{sw:1.5});}
    if(n.frame)o+=attr(K.rect(b.x,fy,b.w,b.h-b.top,{r:10,fill:n.frame==='solid'?'#fbfcfd':'none',st:n.frame==='solid'?t[1]:t[1],sw:1.3,d:n.frame==='dashed'?'6 4':null}),'data-frame="'+n.id+'"');
    if(lab){var lp=labelPos(n,g);g.top+=K.enter(K.text(lp.x,lp.y,n.label,{fs:13,c:t[2],w:700,plate:1}),on(n.id,T),n.id+'.l');}   /* group names sit above connectors (white plate) */
    (b.seps||[]).forEach(function(s){o+=K.line(s.x,s.y0-4,s.x,s.y1+4,K.TONE.red[1],{d:'4 4',sw:1.3})+K.text(s.x,s.y1+24,n.sep,{fs:12,c:K.TONE.red[2],a:'middle'}).replace(/<text /,'<text data-free="1" ');});
    (b.hseps||[]).forEach(function(s){var lw=K.tw(n.sep,12)+8;o+=K.line(s.x0+lw,s.y,s.x1,s.y,K.TONE.red[1],{d:'4 4',sw:1.3})+K.text(s.x0,s.y+4,n.sep,{fs:12,c:K.TONE.red[2],a:'start'}).replace(/<text /,'<text data-free="1" ');});
    if(n.L==='split'){b.divs.forEach(function(d){if(!b.v){o+=K.line(d.x,d.y0,d.x,d.y1,C.edge,{d:'4 4',sw:1.2});
          if(n.arrow)o+=K.text(d.x,b.my-14,n.arrow,{fs:12,c:C.text,a:'middle',w:700,plate:1}).replace(/<text /,'<text data-free="1" ')+K.line(d.x-14,b.my,d.x+12,b.my,C.faint,{sw:1.5})+K.arrow(d.x+14,b.my,C.faint);}
        else o+=K.line(d.x0,d.y,d.x1,d.y,C.edge,{d:'4 4',sw:1.2})+(n.arrow?K.text((d.x0+d.x1)/2,d.y+20,'↓ '+n.arrow,{fs:12,c:C.text,a:'middle',w:700}):'');});}
    if(n.L==='stack'&&b.free)o+=K.rect(b.free.x,b.free.y,b.free.w,b.free.h,{r:6,fill:'#fff',st:C.edge,d:'4 4'})+K.text(b.free.x+b.free.w/2,b.free.y+b.free.h/2+4,n.free,{fs:12,c:C.muted,a:'middle'});
    if(n.L==='lifelines')n.kids.forEach(function(a,i){o+=K.line(b.ax[i],b.cy0+b.ah,b.ax[i],b.cy1,C.edge,{d:'3 4',sw:1.2});});
    if(n.bracket){var bx=b.x+b.w-b.pr+(n.frame?b.pl:0)+10,y0=n.L==='stack'&&b.free?b.free.y:b.cy0,y1=b.cy1,lb=wrap(n.bracket,12,b.x+b.w-bx-14);
      o+=K.line(bx,y0,bx,y1,C.faint,{sw:1.5})+K.line(bx-5,y0,bx,y0,C.faint,{sw:1.5})+K.line(bx-5,y1,bx,y1,C.faint,{sw:1.5});
      lb.forEach(function(l,k){o+=K.text(bx+8,(y0+y1)/2-(lb.length-1)*8+k*16+4,l,{fs:12,c:C.text,w:700});});}
    var bot=b.y+b.h-b.fb;
    if(n.banner){var bt=K.TONE[n.banner.tone];bot-=36;o+=K.rect(b.x+b.pl,bot+6,b.w-b.pl-b.pr,28,{r:6,fill:bt[0],st:bt[1]})+K.text(b.x+b.pl+(b.w-b.pl-b.pr)/2,bot+24,n.banner.text,{fs:12,c:bt[2],a:'middle',w:700});}
    if(b.nl.length){var ny=bot-b.nl.length*16-8;b.nl.forEach(function(l,k){o+=K.text(b.x+b.pl+(b.w-b.pl-b.pr)/2,ny+16+k*16,l,{fs:12,c:C.text,a:'middle'});});}
    if(n.L==='split')b.hdr.forEach(function(h){var tt=K.TONE[h.p.tone];o+=K.enter(K.text(h.x,h.y,h.p.label,{fs:14,c:tt[2],a:h.a,w:700}),on(h.p.id,T),h.p.id+'.h');});
    return o?K.enter(o,on(n.id,T),n.id):'';}
  function messages(n,T,g){var b=g.B[n.id],o='';
    n.msgs.forEach(function(m,k){var r=b.rows[k],u=CH.v(m.key,'reveal',T,1),xa=b.ax[m.a],xb=b.ax[m.b],c=m.dashed?C.muted:C.blue,s='';if(u<=0)return;
      if(r.self){var w=30,p=[[xa,r.y-8],[xa+w,r.y-8],[xa+w,r.y+8],[xa+4,r.y+8]];s+=K.wire(u<1?trim(p,K.plen(p)*u):p,c,{sw:1.5,d:m.dashed?'5 4':null});if(u>.98)s+=head(p,c);
        r.ln.forEach(function(l,j){s+=K.text(xa+w+6,r.y-8+j*LH+4,l,{fs:12,c:C.text,w:j?400:700});});}
      else{var p2=[[xa,r.y],[xb,r.y]];s+=K.line(xa,r.y,xa+(xb-xa)*Math.max(.001,u),r.y,c,{sw:1.6,d:m.dashed?'5 4':null});if(u>.98)s+=head(p2,c);
        var cx=(xa+xb)/2;r.ln.forEach(function(l,j){s+=K.text(cx,r.y-6-(r.ln.length-1-j)*LH,l,{fs:12,c:m.dashed?C.text:C.blueText,a:'middle',w:j?400:700,halo:1});});}
      o+=K.enter(s,Math.min(1,u*1.5),m.key);});
    return o;}
  /* a number badge on its part: a box's top-right corner (on the border), right after a group's name, or at the top
     right of a group's content; links and messages carry theirs in their label text */
  function badge(x,y,txt,id,u){var w=Math.max(18,K.tw(txt,11)+8);
    return K.enter(K.rect(x-w/2,y-9,w,18,{r:9,fill:'#fff',st:C.blue,sw:1.4})+K.text(x,y+4,txt,{fs:11,c:C.blueText,a:'middle',w:700}).replace(/<text /,'<text data-mark="'+txt+'" '),u,'mk'+id);}
  function marks(T,g){var o='';for(var id in MK){var ms=MK[id],txt=mkText(id),u=CH.v('mk'+ms[0].i,'on',T,1),kind=ms[0].kind;
      if(kind==='l'||kind==='m')continue;var b=g.B[id];if(!b)continue;
      if(kind==='e')o+=badge(b.x+b.w-16,b.y,txt,id,u);
      else{var n=null;(function f(x){if(x.t==='c'){if(x.id===id)n=x;else x.kids.forEach(f);}})(R);if(!n)continue;
        if(n.label&&!g.inSplit[n.id]){var lp=labelPos(n,g);o+=badge(lp.x+K.tw(n.label,13)+16,lp.y-4,txt,id,u);}
        else{var hd=null;for(var pid in g.B){var pb=g.B[pid];(pb.hdr||[]).forEach(function(h){if(h.p.id===id)hd=h;});}
          if(hd){var hw=K.tw(n.label,14);o+=badge((hd.a==='middle'?hd.x+hw/2:hd.x+hw)+16,hd.y-5,txt,id,u);}
          else{var c=cbox(n,g);if(c)o+=badge(c.x+c.w-16,c.y,txt,id,u);}}}}
    return o;}
  function draw(T,g){var cs='',ms='',es='',ls='',ts='';g.top='';
    (function walk(n){if(n.t==='e'){es+=element(n,T,g);return;}cs+=container(n,T,g);n.kids.forEach(walk);if(n.L==='lifelines')ms+=messages(n,T,g);})(R);
    LK.forEach(function(l,k){ls+=link(l,k,T,g);ts+=token(l,k,T,g);});
    return cs+ms+ls+g.top+es+marks(T,g)+ts+pathTokens(T,g)+stepList(T,g)+legend(g)+K.text(g.W,g.H-4,D.labels.data_kind,{fs:12,c:C.muted,a:'end'});}
  function stats(){return {left:[]};}
  function probe(T){var S=D.steps;if(!S)return {};var k=0;S.t0.forEach(function(t,i){if(t<=T+1e-9)k=i;});return {step:T>=S.total-1e-9?S.n:k};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe,notes:function(g){return g.notes;}};
};
