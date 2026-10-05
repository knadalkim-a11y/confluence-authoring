/* Scene kind "diagram": components in layers (left to right on wide screens, top to bottom on
   phones), the connections between them, and optional numbered steps a request follows.
   Routing is deterministic and never crosses a box (visual_spec.diagram_data enforces it):
   adjacent layers join by a straight line between spread ports, neighbours in one layer by a
   short line, longer jumps by a lane outside every box. Two-way pairs run as parallel lines.
   The step list stays in the picture (print/no-JS keep the story); playback highlights the
   current step and moves one token along its path. */
CA_SCENES['diagram']=function(D,K,GR){
  var C=K.C,LY=D.layers,E=D.edges,S=D.steps,n=S.length,end=D.time.end,CH=CA_CHOREO(D.cues,K);   /* default choreography from visual_spec */
  var LINE='#868e96',PAST='#4dabf7';
  var TY={system:{fill:'#fff',st:'#adb5bd'},person:{fill:'#fff',st:'#adb5bd',round:1},ai:{fill:C.purpleSoft,st:'#9775fa'},
    data:{fill:C.greenSoft,st:'#69db7c'},external:{fill:C.paper2,st:'#adb5bd',d:'4 3'}};
  var TYNAME=D.types,ND={},PAIR={};
  LY.forEach(function(ly,i){ly.nodes.forEach(function(x,j){ND[x.id]={d:x,l:i,j:j,k:ly.nodes.length};});});
  E.forEach(function(e){PAIR[e.a+'>'+e.b]=1;});
  function two(e){return !!PAIR[e.b+'>'+e.a];}
  var MARK=E.map(function(){return '';});S.forEach(function(st){MARK[st.edges[0]]+=st.mark;});
  function lab(i){var e=E[i];return e.label?(MARK[i]?MARK[i]+' ':'')+e.label:'';}
  /* a bent connection's spine belongs to its end in the earlier layer (or the earlier box of a side pair): a fan-out
     and both directions of a pair share it */
  function owner(e){var A=ND[e.a],B=ND[e.b];return (A.l<B.l||(A.l===B.l&&A.j<B.j))?e.a:e.b;}
  function between(i,r){var a=ND[E[i].a].l,b=ND[E[i].b].l;return E[i].route==='next'&&Math.min(a,b)===r;}
  function wrap(s,fs,w){var out=[],cur='';s.split(' ').forEach(function(wd){var c=cur?cur+' '+wd:wd;if(!cur||K.tw(c,fs)<=w)cur=c;else{out.push(cur);cur=wd;}});if(cur)out.push(cur);return out;}
  function attr(svg,a){return svg.replace('<text ','<text '+a+' ');}
  function hits(b,list){for(var i=0;i<list.length;i++){var f=list[i];if(Math.min(b.x1,f.x1)>Math.max(b.x0,f.x0)&&Math.min(b.y1,f.y1)>Math.max(b.y0,f.y0))return true;}return false;}

  function needW(){var w=LY.length*92+8;for(var r=0;r<LY.length-1;r++){var mw=0,c=0;E.forEach(function(e,i){if(between(i,r)&&lab(i)){mw=Math.max(mw,K.tw(lab(i),12));c++;}});
      w+=Math.max(44,Math.min(220,mw+24+(c>2?14*(c-2):0)));}return w;}
  /* rotate to the phone layout whenever the row would squeeze boxes or labels (not only below 560 px) */
  function geom(W){var g={W:W,v:W<560||W<needW(),N:{}},L=LY.length,maxK=0,over=[],under=[];
    LY.forEach(function(ly){maxK=Math.max(maxK,ly.nodes.length);});
    E.forEach(function(e,i){if(e.route==='over')over.push(i);if(e.route==='under')under.push(i);});
    var GH=D.groups.length?24:0,side=E.some(function(e){return e.route==='side';}),widths={},X=[],gap=[],m=GH?12:4;
    function crowd(r){var mw=0,c=0;E.forEach(function(e,i){if(between(i,r)&&lab(i)){mw=Math.max(mw,K.tw(lab(i),12));c++;}});return [mw,c];}
    if(!g.v){for(var i=0;i<L-1;i++){var cr=crowd(i);   /* more labels in one gap -> wider gap, so a fan-out spreads them */
        gap.push(Math.max(56,Math.min(220,cr[0]+30+(cr[1]>2?14*(cr[1]-2):0))));}
      var sg=gap.reduce(function(a,b){return a+b;},0),nw=(W-2*m-sg)/L;
      if(nw>170){m+=(nw-170)*L/2;nw=170;}
      if(nw<104&&sg>56*(L-1)){var take=Math.min(sg-56*(L-1),(104-nw)*L);gap=gap.map(function(x){return x-take*(x-56)/(sg-56*(L-1));});sg-=take;nw=(W-2*m-sg)/L;}
      for(i=0;i<L;i++)X.push(i===0?m:X[i-1]+nw+gap[i-1]);
      LY.forEach(function(ly){ly.nodes.forEach(function(x){widths[x.id]=nw;});});g.nw=nw;}
    else{g.sl=6+(over.length?over.length*10+4:0);g.sr=6+(under.length?under.length*10+4:0);if(GH){g.sl+=6;g.sr+=6;}
      var avail=W-g.sl-g.sr;g.hg={};
      LY.forEach(function(ly,r){var k=ly.nodes.length,hs=[];for(var j=0;j<k-1;j++){var mw=0;E.forEach(function(e,i){if(e.route==='side'&&ND[e.a].l===r&&Math.min(ND[e.a].j,ND[e.b].j)===j&&lab(i))mw=Math.max(mw,K.tw(lab(i),12)+16);});hs.push(Math.max(12,mw));}
        g.hg[r]=hs;var sh=hs.reduce(function(a,b){return a+b;},0),w=Math.min(160,(avail-sh)/k);ly.nodes.forEach(function(x){widths[x.id]=w;});});g.avail=avail;}
    /* text inside boxes: name up to two lines (13 -> 12 px), sub on one line or not at all at this width */
    var H0=0,noSub=false;
    LY.forEach(function(ly){ly.nodes.forEach(function(x){var w=widths[x.id],fs=g.v?13:15,ln=[x.name];   /* one line at 15 or 13 px if it fits, else two */
      if(K.tw(x.name,fs)>w-14){fs=g.v?12:13;if(K.tw(x.name,fs)>w-12)ln=wrap(x.name,fs,w-12);}
      g.fsub=g.v?11:12;if(x.sub&&K.tw(x.sub,g.fsub)>w-12)noSub=true;g.N[x.id]={w:w,fs:fs,lines:ln};});});
    var anySub=!noSub&&LY.some(function(ly){return ly.nodes.some(function(x){return x.sub;});});
    LY.forEach(function(ly){ly.nodes.forEach(function(x){var b=g.N[x.id];b.bh=(b.lines.length-1)*(b.fs+5)+b.fs+(anySub&&x.sub?g.fsub+6:0)+3;H0=Math.max(H0,b.bh+(g.v?12:20));});});
    g.noSub=noSub;g.h=H0;
    var y0,bottom;
    if(!g.v){var vg=side?30:16,ext=maxK*H0+(maxK-1)*vg;y0=6+(over.length?over.length*12+8:0)+(GH?GH+8:0);
      LY.forEach(function(ly,i){var k=ly.nodes.length,st=y0+(ext-(k*H0+(k-1)*vg))/2;
        ly.nodes.forEach(function(x,j){var b=g.N[x.id];b.x=X[i];b.y=st+j*(H0+vg);});});
      bottom=y0+ext+(GH?10:0);g.lanes={};
      over.forEach(function(ei,q){g.lanes[ei]=y0-(GH?GH+8:0)-8-q*12;});
      under.forEach(function(ei,q){g.lanes[ei]=bottom+10+q*12;});
      bottom+=under.length?under.length*12+8:0;
      g.groups=D.groups.map(function(gp){return {x:X[gp.a]-10,y:y0-GH-6,w:X[gp.b]+nw+20-X[gp.a],h:ext+GH+16,label:gp.label};});}
    else{var gvs=[],rowY=[];
      LY.forEach(function(ly,i){var k=ly.nodes.length,w=widths[ly.nodes[0].id],hs=g.hg[i],sh=hs.reduce(function(a,b){return a+b;},0),x=g.sl+(g.avail-(k*w+sh))/2;
        ly.nodes.forEach(function(nd,j){g.N[nd.id].x=x;x+=w+(hs[j]||0);});});
      function bent(e){var A=g.N[e.a],B=g.N[e.b];return Math.min(A.x+A.w,B.x+B.w)-Math.max(A.x,B.x)<20;}
      for(var r=0;r<L-1;r++){var cr=crowd(r);var own={};E.forEach(function(e,i){if(between(i,r)&&bent(e))own[owner(e)]=1;});var ns=Object.keys(own).length;   /* one bend per spine */
        gvs.push(Math.max(34+9*Math.min(3,Math.max(0,cr[1]-1)),ns?24+10*ns+16*Math.ceil(cr[1]/2):0)+(ns&&D.groups.some(function(gp){return gp.a===r+1;})?GH:0));}   /* a group header in the gap keeps the bends and labels clear of it */
      y0=6+(D.groups.some(function(gp){return gp.a===0;})?GH+2:0);var yy=y0;   /* a later group's header sits in the gap above it */
      LY.forEach(function(ly,i){rowY.push(yy);ly.nodes.forEach(function(nd){g.N[nd.id].y=yy;});yy+=H0+(gvs[i]||0);});
      bottom=rowY[L-1]+H0+(GH?8:0);g.lanes={};
      over.forEach(function(ei,q){g.lanes[ei]=6+q*10;});
      under.forEach(function(ei,q){g.lanes[ei]=W-6-q*10;});
      g.rowY=rowY;g.gvs=gvs;
      g.groups=D.groups.map(function(gp){return {x:g.sl-8,y:rowY[gp.a]-GH-2,w:g.avail+16,h:rowY[gp.b]+H0+10-(rowY[gp.a]-GH-2),label:gp.label};});}
    /* ports: one slot per connection (a two-way pair shares one), spread along the face */
    var faces={};
    function face(e,end){var A=ND[e.a],B=ND[e.b],me=end?B:A,ot=end?A:B;
      if(e.route==='next')return g.v?(me.l<ot.l?'b':'t'):(me.l<ot.l?'r':'l');
      if(e.route==='side')return g.v?(me.j<ot.j?'r':'l'):(me.j<ot.j?'b':'t');
      if(e.route==='over')return g.v?'l':'t';return g.v?'r':'b';}
    E.forEach(function(e,i){[0,1].forEach(function(end){var id=end?e.b:e.a,f=face(e,end),key=id+f;(faces[key]=faces[key]||[]);
      var pk=[e.a,e.b].sort().join('|');if(faces[key].every(function(s){return s.pk!==pk;}))faces[key].push({pk:pk,other:end?e.a:e.b});});});
    function centre(id){var b=g.N[id];return [b.x+b.w/2,b.y+H0/2];}
    function port(id,f,other){var b=g.N[id],list=faces[id+f],horiz=f==='t'||f==='b',len=horiz?b.w:H0;
      list.sort(function(p,q){var a=centre(p.other),c=centre(q.other);return horiz?a[0]-c[0]:a[1]-c[1];});
      var pk=[id,other].sort().join('|'),idx=0;list.forEach(function(s,k){if(s.pk===pk)idx=k;});
      var sp=Math.min(16,(len-12)/Math.max(1,list.length)),o=(idx-(list.length-1)/2)*sp;
      return f==='r'?[b.x+b.w,b.y+H0/2+o]:f==='l'?[b.x,b.y+H0/2+o]:f==='t'?[b.x+b.w/2+o,b.y]:[b.x+b.w/2+o,b.y+H0];}
    /* straight when the ports line up, otherwise one elbow (K.ortho): never a diagonal. Connections
       in the same gap that start from different boxes get their own spine, spread around the middle;
       connections from one box share its spine, so a fan-out reads as one trunk with branches. */
    var R=E.map(function(e,i){var p=port(e.a,face(e,0),e.b),q=port(e.b,face(e,1),e.a),off=two(e)?(e.a<e.b?4:-4):0;
      if(e.route!=='next'&&e.route!=='side')return {p:p,q:q,off:off};
      var dir=(e.route==='next')!==g.v?'h':'v',s=e.a>e.b?-off:off,m=dir==='h'?0:1,c=1-m;   /* m: main axis index, c: across */
      var A=g.N[e.a],B=g.N[e.b],lo=Math.max(c?A.x:A.y,c?B.x:B.y)+10,hi=Math.min(c?A.x+A.w:A.y+H0,c?B.x+B.w:B.y+H0)-10;
      if(lo<=hi){var v=Math.max(lo,Math.min(hi,(p[c]+q[c])/2));p=p.slice();q=q.slice();p[c]=v;q[c]=v;}   /* the boxes face each other: a straight line */
      p=m?[p[0]+s,p[1]]:[p[0],p[1]+s];q=m?[q[0]+s,q[1]]:[q[0],q[1]+s];
      return {p:p,q:q,off:off,dir:dir,m:m,s:s,bend:Math.abs(p[1-m]-q[1-m])>0.5,key:dir+Math.round(Math.min(p[m],q[m]))+'/'+Math.round(Math.max(p[m],q[m]))};});
    var spines={};R.forEach(function(r,i){if(!r.bend)return;var src=owner(E[i]),k=spines[r.key]=spines[r.key]||[];if(k.every(function(x){return x[0]!==src;}))k.push([src,(src===E[i].a?r.p:r.q)[1-r.m]]);});
    Object.keys(spines).forEach(function(k){spines[k].sort(function(a,b){return a[1]-b[1];});});
    g.E=E.map(function(e,i){var r=R[i],p=r.p,q=r.q,off=r.off,pts;
      if(r.dir){if(!r.bend)pts=[p,q];
        else{var list=spines[r.key],idx=0;list.forEach(function(x,k){if(x[0]===owner(e))idx=k;});
          var lo=p[r.m],hi=q[r.m],dn=hi>lo?1:-1;   /* the bend stays outside group boundaries (their titles sit in the gap) */
          g.groups.forEach(function(b){var inP=p[0]>=b.x&&p[0]<=b.x+b.w&&p[1]>=b.y&&p[1]<=b.y+b.h;
            [r.m?b.y:b.x,r.m?b.y+b.h:b.x+b.w].forEach(function(z){if((z-lo)*dn>0&&(hi-z)*dn>0){if(inP)lo=z+dn*4;else hi=z-dn*4;}});});
          var gapw=Math.abs(hi-lo),sp=Math.min(10,Math.max(0,(gapw-24)/Math.max(1,list.length))),at=(lo+hi)/2+(idx-(list.length-1)/2)*sp*dn+r.s;
          pts=K.ortho([p,q],r.dir,at);}}
      else{var ln=g.lanes[i];pts=g.v?[[p[0],p[1]+off],[ln,p[1]+off],[ln,q[1]+off],[q[0],q[1]+off]]:[[p[0]+off,p[1]],[p[0]+off,ln],[q[0]+off,ln],[q[0]+off,q[1]]];}
      return {pts:pts,off:off};});
    /* labels: group headers, then connection labels, then step badges; none may sit on a box */
    var solid=[];LY.forEach(function(ly){ly.nodes.forEach(function(x){var b=g.N[x.id];solid.push({x0:b.x-3,x1:b.x+b.w+3,y0:b.y-3,y1:b.y+H0+3});});});
    var placed=[];
    function area(b,list){var t=0;list.forEach(function(f){var w=Math.min(b.x1,f.x1)-Math.max(b.x0,f.x0),h=Math.min(b.y1,f.y1)-Math.max(b.y0,f.y0);if(w>0&&h>0)t+=w*h;});return t;}
    /* first free candidate; if none is free, the one that overlaps least (boxes weigh more than labels) */
    function put(s,fs,cands){var w=K.tw(s,fs),best=null,bs=1e18,bb=null;cands.some(function(c){var x0=c[2]==='middle'?c[0]-w/2:c[2]==='end'?c[0]-w:c[0],
        b={x0:x0-3,x1:x0+w+3,y0:c[1]-fs-2,y1:c[1]+5},sc=(b.x0<0||b.x1>W?1e9:0)+area(b,solid)*10+area(b,placed);   /* the rendered box is ~1.5em tall */
        if(sc<bs){bs=sc;best=c;bb=b;}return sc===0;});
      placed.push(bb);return best;}
    function along(pts,f){var seg=[],tot=0;for(var i=1;i<pts.length;i++){var l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);seg.push(l);tot+=l;}
      var d=f*tot;for(i=0;i<seg.length;i++){if(d<=seg[i]||i===seg.length-1){var t=seg[i]?d/seg[i]:0;
        return {x:pts[i][0]+(pts[i+1][0]-pts[i][0])*t,y:pts[i][1]+(pts[i+1][1]-pts[i][1])*t,ux:(pts[i+1][0]-pts[i][0])/(seg[i]||1),uy:(pts[i+1][1]-pts[i][1])/(seg[i]||1)};}d-=seg[i];}}
    g.along=along;
    function spread(id,f){return (faces[id+f]||[]).length;}
    g.L=E.map(function(e,i){if(!e.label)return null;var ge=g.E[i],c=[],sa=spread(e.a,face(e,0)),sb=spread(e.b,face(e,1)),
        fr=(sa>sb?[.68,.78,.58,.48,.38,.28]:sb>sa?[.32,.22,.42,.52,.62,.72]:[.5,.38,.62,.28,.72]).concat([.15,.85,.1,.9]);   /* the ends too: a bent route has room near its boxes */
      if((e.route==='over'||e.route==='under')&&g.v){for(var r=Math.min(ND[e.a].l,ND[e.b].l);r<Math.max(ND[e.a].l,ND[e.b].l);r++){var yy=g.rowY[r]+H0+g.gvs[r]/2+4;
          c.push(e.route==='over'?[g.lanes[i]+5,yy,'start']:[g.lanes[i]-5,yy,'end']);}}
      else{var pts=e.route==='next'||e.route==='side'?ge.pts:[ge.pts[1],ge.pts[2]];
        var alt=[];   /* first choice at every point along the line, then the same points with other anchors */
        fr.forEach(function(f){var a=along(pts,f),s=ge.off?(ge.off>0?1:-1)*(e.a>e.b?-1:1):0,nx=-a.uy,ny=a.ux,steep=Math.abs(nx)>Math.abs(ny);
          if(s){var side=[a.x+nx*7*s,a.y+4,nx*s>0?'start':'end'],over=[a.x+nx*10*s,a.y+ny*10*s+4,'middle'];c.push(steep?side:over);alt.push(steep?over:side,[a.x+nx*16*s,a.y+ny*16*s+4,'middle']);}
          else{c.push([a.x,a.y+4,'middle']);alt.push([a.x+7,a.y+4,'start'],[a.x-7,a.y+4,'end']);}});
        c=c.concat(alt);
        if(e.route==='side'){var z=ge.pts[ge.pts.length-1];c.push(g.v?[(ge.pts[0][0]+z[0])/2,ge.pts[0][1]-8,'middle']:[ge.pts[0][0]+6,(ge.pts[0][1]+z[1])/2+4,'start']);}}
      return put(lab(i),12,c);});
    g.B=S.map(function(st,k){if(E[st.edges[0]].label||(k&&S[k-1].edges[0]===st.edges[0]))return null;var ge=g.E[st.edges[0]],c=[];[16,28,40].forEach(function(d){var tot=0;for(var i=1;i<ge.pts.length;i++)tot+=Math.hypot(ge.pts[i][0]-ge.pts[i-1][0],ge.pts[i][1]-ge.pts[i-1][1]);
        var a=along(ge.pts,Math.min(.45,d/tot)),nx=-a.uy,ny=a.ux;[1,-1].forEach(function(s){c.push([a.x+nx*12*s,a.y+ny*12*s+5,'middle']);});});
      return put(MARK[st.edges[0]],14,c);});
    /* group titles last: whichever corner of the boundary is free */
    g.gl=g.groups.map(function(gr){return put(gr.label,12,[[gr.x+8,gr.y+15,'start'],[gr.x+gr.w-8,gr.y+15,'end'],[gr.x+8,gr.y+gr.h-5,'start'],[gr.x+gr.w-8,gr.y+gr.h-5,'end']]);});
    /* step list and legend under the diagram */
    var y=bottom+(n?18:8);g.list=[];
    S.forEach(function(st){var ln=wrap(st.text,g.v?12:13,W-24);g.list.push({y:y,lines:ln,lh:g.v?16:18});y+=ln.length*(g.v?16:18)+(g.v?1:4);});
    var items=[];Object.keys(TYNAME).forEach(function(k){items.push(['type',k,TYNAME[k]]);});
    if(E.some(function(e){return e.dashed;}))items.push(['dash',null,'점선 = '+D.dashed_means]);
    var lx=0,ly2=y+12;g.leg=[];items.forEach(function(it){var w=K.tw(it[2],12)+(it[0]==='type'?20:30);if(lx&&lx+w>W){lx=0;ly2+=18;}g.leg.push([lx,ly2,it]);lx+=w+12;});
    var mw=K.tw(D.labels.data_kind,12);if(items.length&&lx+mw+12>W){ly2+=18;}
    g.markY=ly2;g.H=ly2+6;return g;}

  function poly(pts,c,sw,d){return K.wire(pts,c,{sw:sw,d:d?'5 4':null});}
  function head(pts,c){var p=pts[pts.length-2],q=pts[pts.length-1],dx=q[0]-p[0],dy=q[1]-p[1],l=Math.hypot(dx,dy)||1,ux=dx/l,uy=dy/l,x=q[0],y=q[1];
    return '<path d="M'+K.f(x-8*ux-4.5*uy)+' '+K.f(y-8*uy+4.5*ux)+'L'+K.f(x)+' '+K.f(y)+'L'+K.f(x-8*ux+4.5*uy)+' '+K.f(y-8*uy-4.5*ux)+'Z" fill="'+c+'"/>';}
  function state(T){var done=n>0&&T>=n-1e-9,cur=n?(done?n:Math.min(n-1,Math.floor(T+1e-9))):-1;return {cur:cur,done:done};}
  function draw(T,g){var o='',s=state(T),H0=g.h,es=E.map(function(){return 0;}),act={};
    S.forEach(function(st,k){var v=s.done||k<s.cur?1:k===s.cur?2:0;st.edges.forEach(function(i){es[i]=Math.max(es[i],v);});if(v===2)st.nodes.forEach(function(id){act[id]=1;});});
    g.groups.forEach(function(gr){o+=K.rect(gr.x,gr.y,gr.w,gr.h,{r:8,fill:C.paper2,st:C.rule});});
    /* connection level 0 idle, 1 used, 2 current; fractional while a cue runs (colour and width blend) */
    var lv=E.map(function(e,i){return CH.v('e'+i,'level',T,es[i]);});
    function lcol(v){return v<=1?K.mix(LINE,PAST,v):K.mix(PAST,C.blue,v-1);}
    E.map(function(e,i){return i;}).sort(function(a,b){return lv[a]-lv[b];}).forEach(function(i){var e=E[i],v=lv[i],c=lcol(v),pts=g.E[i].pts;
      o+=poly(pts,c,v<=1?1.4+.4*v:1.8+.6*(v-1),e.dashed).replace('<polyline ','<polyline data-k="e'+i+'" ')+head(pts,c);});
    LY.forEach(function(ly){ly.nodes.forEach(function(x){var b=g.N[x.id],t=TY[x.type],hl=D.highlight.indexOf(x.id)>=0,on=act[x.id];
      var a=CH.v('n:'+x.id,'act',T,on?1:0),p0=CH.since('n:'+x.id,'pop',T),sc=p0==null?0:.04*K.pop(T,p0,.4),dx=b.w*sc/2,dy=H0*sc/2;   /* a box that joins the step pops once */
      o+=K.rect(b.x-dx,b.y-dy,b.w+2*dx,H0+2*dy,{r:t.round?H0/2:8,fill:hl?C.blueSoft:t.fill,st:hl?C.blue:K.mix(t.st,C.blue,a),sw:hl?Math.max(1.6,1.2+a):1.2+a,d:a>.5||hl?null:t.d}).replace('<rect ','<rect data-k="n:'+x.id+'" data-solid="'+x.id+'" ');
      var sub=x.sub&&!g.noSub,nl=b.lines.length,lh=b.fs+5,top=b.y+(H0-b.bh)/2+b.fs*0.9;   /* block centred: names, then sub */
      b.lines.forEach(function(s,k){o+=attr(K.text(b.x+b.w/2,top+k*lh,s,{fs:b.fs,c:C.ink,a:'middle',w:700}),'data-in="'+x.id+'"');});
      if(sub)o+=attr(K.text(b.x+b.w/2,top+(nl-1)*lh+g.fsub+7,x.sub,{fs:g.fsub,c:C.muted,a:'middle'}),'data-in="'+x.id+'"');});});
    if(n&&!s.done){
      /* drawn under the labels; one token per route at the shared pace (K.M.speed), eased at both ends,
         finishing within the step; it travels the connections only and passes through a box unseen */
      S[s.cur].paths.forEach(function(r,ri){var legs=[],tot=0;
        r.forEach(function(i,k){if(k){var a=g.E[r[k-1]].pts,b=g.E[i].pts,z=a[a.length-1];tot+=Math.hypot(b[0][0]-z[0],b[0][1]-z[1]);}   /* through the box, unseen */
          legs.push([tot,K.plen(g.E[i].pts),i]);tot+=K.plen(g.E[i].pts);});
        var t0=s.cur+K.wall(D.rate,s.cur,.2),dur=Math.min(.75,Math.max(.6,tot/K.M.speed)),d=K.ease(T,t0,dur)*tot;if(T<t0)return;   /* leaves with the new step's rise (0.8 of the old step's fall), arrives before the next step */
        legs.forEach(function(L,k){if(d<L[0]-1e-9||d>L[0]+L[1]+1e-9)return;var a=K.at(g.E[L[2]].pts,d-L[0]);
          o+=K.token(a.x,a.y,'s'+s.cur+'r'+ri+'k'+k,5,C.blue).replace('/>',' stroke="#fff" stroke-width="2"/>');});});}
    g.groups.forEach(function(gr,k){var q=g.gl[k];o+=attr(K.text(q[0],q[1],gr.label,{fs:12,c:C.text,a:q[2],w:700,plate:1}),'data-free="1"');});
    E.forEach(function(e,i){var p=g.L[i],u=K.clamp(lv[i]-1);if(p)o+=attr(K.text(p[0],p[1],lab(i),{fs:12,c:K.mix(C.text,C.blueText,u),a:p[2],plate:1,w:u>.5?700:400}),'data-free="1" data-k="t'+i+'"');});
    S.forEach(function(st,k){var p=g.B[k];if(p)o+=attr(K.text(p[0],p[1],MARK[st.edges[0]],{fs:14,c:C.blueText,a:'middle',w:700,halo:1}),'data-free="1"');});
    S.forEach(function(st,k){var it=g.list[k],now=!s.done&&k===s.cur,on=CH.v('l'+k,'on',T,now?2:s.done||k<s.cur?1:0),c=on<=1?K.mix(C.muted,C.text,on):K.mix(C.text,C.blueText,on-1);
      it.lines.forEach(function(ln,j){o+=attr(K.text(j?20:0,it.y+j*it.lh,(j?'':st.mark+' ')+ln,{fs:g.v?12:13,c:c,w:on>1.5?700:400}),'data-k="l'+k+'.'+j+'"');});});
    g.leg.forEach(function(L){var x=L[0],y=L[1],it=L[2];
      if(it[0]==='type'){var t=TY[it[1]];o+=K.rect(x,y-9,12,11,{r:3,fill:t.fill,st:t.st,d:t.d})+K.text(x+17,y,it[2],{fs:12,c:C.muted});}
      else o+=poly([[x,y-4],[x+22,y-4]],LINE,1.4,1)+K.text(x+28,y,it[2],{fs:12,c:C.muted});});
    o+=K.text(g.W,g.markY,D.labels.data_kind,{fs:12,c:C.muted,a:'end'});
    return o;}
  function stats(){return {left:[]};}
  function probe(T){return {step:state(T).cur};}
  return {end:end,geom:geom,draw:draw,stats:stats,probe:probe};
};
