/* SVG string helpers shared by live grammars. Pure functions: no DOM access, so the
   same code renders the animated view in the browser and the static fallback in Node.
   Palette: Open Color values (MIT). Fills use the base hue; text that must stay legible
   on white uses the darker *Text variants. */
var CA_KIT=(function(){
  /* Fills/lines may use any token. Text must use a *Text token, ink, text or muted: each is
     >= 4.5:1 on white (WCAG AA for small text); faint is for rails/grid/separators only. */
  var C={ink:'#343a40',text:'#495057',muted:'#697077',faint:'#adb5bd',rule:'#e9ecef',edge:'#ced4da',rail:'#ced4da',
    blue:'#228be6',blueText:'#1971c2',blueSoft:'#e7f5ff',blueMid:'#a5d8ff',
    red:'#fa5252',redText:'#c92a2a',redSoft:'#fff5f5',redRail:'#ffc9c9',
    amber:'#fab005',amberText:'#a85a00',amberSoft:'#fff9db',amberCell:'#ffd43b',band:'#fff9db',
    green:'#40c057',greenText:'#237032',greenSoft:'#ebfbee',greenPill:'#d3f9d8',
    purple:'#845ef7',purpleText:'#7048e8',purpleSoft:'#f3f0ff',
    paper:'#fff',paper2:'#f8f9fa',hotPaper:'#fff5f5'};
  /* Pill kinds: [background, text]; every pair >= 4.5:1. */
  var PILL={ok:['#d3f9d8','#237032'],warn:['#fff3bf','#a85a00'],hot:['#e03131','#fff'],info:['#e7f5ff','#1864ab'],bad:['#ffe3e3','#c92a2a'],purple:['#f3f0ff','#6741d9']};
  function f(v){return Math.round(v*10)/10;}
  function clamp(v){return v<0?0:v>1?1:v;}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  /* halo: white outline under the glyphs, for labels placed over lines, areas or dots. */
  function halo(o){return o.halo?' stroke="#fff" stroke-width="3" stroke-linejoin="round" paint-order="stroke"':'';}
  /* plate: white backing behind a label that crosses a reference line (estimated width). */
  function text(x,y,s,o){o=o||{};if(o.plate){var pw=tw(s,o.fs||12)+4,px=o.a==='end'?x-pw+2:o.a==='middle'?x-pw/2:x-2,q={};for(var k in o)if(k!=='plate')q[k]=o[k];
    return rect(px,y-(o.fs||12)+1,pw,(o.fs||12)+3,{r:2,fill:'#fff'})+text(x,y,s,q);}
    return '<text x="'+f(x)+'" y="'+f(y)+'" font-size="'+(o.fs||12)+'" fill="'+(o.c||C.muted)+'"'+
    (o.a?' text-anchor="'+o.a+'"':'')+(o.w?' font-weight="'+o.w+'"':'')+halo(o)+'>'+esc(s)+'</text>';}
  /* One text run with coloured/bold parts: parts = [[string, colour|null, bold]]. */
  function rich(x,y,parts,o){o=o||{};return '<text x="'+f(x)+'" y="'+f(y)+'" font-size="'+(o.fs||12)+'" fill="'+(o.c||C.muted)+'"'+(o.a?' text-anchor="'+o.a+'"':'')+halo(o)+'>'+
    parts.map(function(p){return '<tspan'+(p[1]?' fill="'+p[1]+'"':'')+(p[2]?' font-weight="700"':'')+'>'+esc(p[0])+'</tspan>';}).join('')+'</text>';}
  /* Conservative advance-width estimate for layout (bold Hangul <= 1em, digits/Latin <= 0.62em);
     errs wide so chips never clip their text in common Korean UI fonts. */
  function tw(s,fs){var w=0;String(s).split('').forEach(function(ch){var c=ch.charCodeAt(0);w+=c>=0x1100?1.0:ch===' '?0.3:/[.,·:()/]/.test(ch)?0.36:0.62;});return w*fs;}
  function rect(x,y,w,h,o){o=o||{};return '<rect x="'+f(x)+'" y="'+f(y)+'" width="'+f(Math.max(0,w))+'" height="'+f(Math.max(0,h))+
    '" rx="'+(o.r==null?4:o.r)+'" fill="'+(o.fill||'none')+'"'+(o.st?' stroke="'+o.st+'" stroke-width="'+(o.sw||1)+'"':'')+
    (o.d?' stroke-dasharray="'+o.d+'"':'')+(o.op!=null?' opacity="'+f(o.op*100)/100+'"':'')+'/>';}
  /* Rounded label chip; kind: ok | warn | hot | info. Returns svg; anchor = middle|start|end. */
  function pill(x,y,s,kind,o){o=o||{};var fs=o.fs||11,w=tw(s,fs)+14,h=fs+8,x0=o.a==='start'?x:o.a==='end'?x-w:x-w/2,
    k=PILL[kind||'info'];
    return rect(x0,y-h/2,w,h,{r:h/2,fill:k[0]})+text(x0+w/2,y+fs*0.36,s,{fs:fs,c:k[1],a:'middle',w:700});}
  function line(x1,y1,x2,y2,c,o){o=o||{};return '<line x1="'+f(x1)+'" y1="'+f(y1)+'" x2="'+f(x2)+'" y2="'+f(y2)+'" stroke="'+c+
    '" stroke-width="'+(o.sw||1)+'"'+(o.d?' stroke-dasharray="'+o.d+'"':'')+(o.op!=null?' opacity="'+o.op+'"':'')+(o.cap?' stroke-linecap="round"':'')+'/>';}
  function dot(x,y,r,c,op){return '<circle cx="'+f(x)+'" cy="'+f(y)+'" r="'+r+'" fill="'+c+'"'+(op!=null&&op<1?' opacity="'+f(op*100)/100+'"':'')+'/>';}
  function ring(x,y,r,fill,st,sw){return '<circle cx="'+f(x)+'" cy="'+f(y)+'" r="'+r+'" fill="'+fill+'" stroke="'+st+'" stroke-width="'+(sw||1.5)+'"/>';}
  function path(d,fill,op){return '<path d="'+d+'" fill="'+fill+'"'+(op!=null?' opacity="'+op+'"':'')+'/>';}
  function arrow(x,y,c){return '<path d="M'+f(x-6)+' '+f(y-4)+'L'+f(x)+' '+f(y)+'L'+f(x-6)+' '+f(y+4)+'" fill="none" stroke="'+c+'" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>';}
  /* Thick utilisation gauge with a percentage label below (green < 100%, red at the limit). */
  function gauge(x,y,w,frac,hot,o){o=o||{};var fr=clamp(frac),c=hot?C.red:C.green,s=rect(x,y,w,6,{r:3,fill:C.rule})+rect(x,y,w*fr,6,{r:3,fill:c});
    if(!o.noLabel)s+=text(x+w/2,y+22,Math.round(fr*100)+'%',{fs:o.fs||13,c:hot?C.redText:C.greenText,a:'middle',w:700});return s;}
  function num(v,d){return Number(v).toFixed(d==null?1:d);}
  /* Integer with thousands separators, locale independent. */
  function grp(v){var n=Math.round(v),s=String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g,',');return (n<0?'-':'')+s;}
  /* Motion and wiring parts shared by every scene; their limits are checked by visual_gates.MOTION_JS.
     ortho: a polyline made orthogonal - every diagonal step becomes an elbow (along the main axis to
     the midpoint `at`, across, then on), so connectors never run crooked. dir 'h' | 'v'. */
  function ortho(pts,dir,at){var o=[pts[0]];for(var i=1;i<pts.length;i++){var a=o[o.length-1],b=pts[i];
      if(Math.abs(a[0]-b[0])>0.5&&Math.abs(a[1]-b[1])>0.5){if(dir==='v'){var my=at!=null?at:(a[1]+b[1])/2;o.push([a[0],my],[b[0],my]);}
        else{var mx=at!=null?at:(a[0]+b[0])/2;o.push([mx,a[1]],[mx,b[1]]);}}
      o.push(b);}return o;}
  /* wire: draws a connector; data-wire lets the gate verify it has no diagonal segment. */
  function wire(pts,c,o){o=o||{};return '<polyline data-wire="1" points="'+pts.map(function(p){return f(p[0])+' '+f(p[1]);}).join(' ')+'" fill="none" stroke="'+c+'" stroke-width="'+(o.sw||1.5)+'"'+
    (o.d?' stroke-dasharray="'+o.d+'"':'')+(o.op!=null?' opacity="'+o.op+'"':'')+' stroke-linejoin="round"/>';}
  function plen(pts){var t=0;for(var i=1;i<pts.length;i++)t+=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);return t;}
  /* point at distance d along a polyline (clamped), with the unit direction there */
  function at(pts,d){d=Math.max(0,d);for(var i=1;i<pts.length;i++){var l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);
      if(d<=l||i===pts.length-1){var r=l?Math.min(1,d/l):0;return {x:pts[i-1][0]+(pts[i][0]-pts[i-1][0])*r,y:pts[i-1][1]+(pts[i][1]-pts[i-1][1])*r,ux:(pts[i][0]-pts[i-1][0])/(l||1),uy:(pts[i][1]-pts[i-1][1])/(l||1)};}d-=l;}
    return {x:pts[0][0],y:pts[0][1],ux:1,uy:0};}
  /* Moving things the reader follows. M.speed: px per model second for travel along a wire;
     M.turn: revolutions per model second for anything that circles. Scenes take their pace from here,
     and the gate rejects any token faster than MOTION_MAX px per wall second. */
  var M={speed:150,turn:.45,fade:.35};
  /* token: a moving dot; id must stay the same while one thing moves (a new trip = a new id). */
  function token(x,y,id,r,c,op){return dot(x,y,r,c,op).replace('<circle ','<circle data-token="'+esc(id)+'" ');}
  /* ease: 0..1 over dur seconds from t0 (smooth start and end); for anything that appears or changes state */
  /* Motion math (v0.12, docs/design/motion-concept-architecture.md L1). Closed forms only: the value at T
     never depends on earlier frames, so seek, print, the Node static scene and model checks keep working.
     Two kinds of time math exist in scenes and stay apart:
       data interpolation (load, progress, a series between samples) follows the model, linear, untouched;
       presentation (appear, leave, switch state, move) uses the curves and durations below. */
  function bez(x1,y1,x2,y2){function b(t,a,c){return 3*a*t*(1-t)*(1-t)+3*c*t*t*(1-t)+t*t*t;}
    return function(u){if(u<=0)return 0;if(u>=1)return 1;var lo=0,hi=1,t=u;for(var i=0;i<24;i++){if(b(t,x1,x2)<u)lo=t;else hi=t;t=(lo+hi)/2;}return b(t,y1,y2);};}
  /* out: arrive and settle (entrances); in: leave and accelerate (exits, falling); inOut: move from rest to rest */
  /* inOut is the symmetric smoothstep (peak speed 1.5x the average): moving things keep the shared pace;
     a steeper inOut (0.4,0,0.2,1 peaks ~2.4x) pushed diagram tokens past the speed gate */
  var CURVE={linear:function(u){return u;},out:bez(0,0,.2,1),in:bez(.4,0,1,1),inOut:function(u){u=clamp(u);return u*u*(3-2*u);}};
  /* default durations in seconds (design doc, section 4) */
  var DUR={enter:.4,exit:.25,color:.25,emph:.4,settle:.4,stagger:.06};
  /* tween: progress 0..1 of a presentation change that starts at t0 and lasts dur, shaped by a curve */
  function tween(T,t0,dur,curve){var u=dur>0?clamp((T-t0)/dur):(T>=t0?1:0);return (CURVE[curve||'out']||CURVE.out)(u);}
  /* spring: step response of a damped spring, 0 at t<=0, overshoots then settles at 1. zeta < 1 bounces.
     For emphasis only (a box that pops when its step starts), never for a position that shows data. */
  function spring(t,zeta,freq){if(t<=0)return 0;var z=zeta==null?.6:zeta,w=2*Math.PI*(freq||2.2);if(z>=1)return 1-Math.exp(-w*t)*(1+w*t);
    var wd=w*Math.sqrt(1-z*z);return 1-Math.exp(-z*w*t)*(Math.cos(wd*t)+z*w/wd*Math.sin(wd*t));}
  /* pop: emphasis that rises with the spring and returns to rest: 0 -> peak -> 0 within ~dur */
  function pop(T,t0,dur){var t=T-t0,d=dur||DUR.emph;if(t<=0||t>=d)return 0;return Math.sin(Math.PI*t/d)*(.7+.3*spring(t,.5,1/d));}
  /* approach: a shown value gliding from `from` to `to` (a counter, a gauge); exact `to` after `settle` s */
  function approach(from,to,t,settle){var st=settle||DUR.settle;if(t<=0)return from;if(t>=st)return to;return to+(from-to)*Math.exp(-5.3*t/st);}
  /* stagger: start time of item i of n inside a group that starts at t0; spread capped at `total` seconds */
  function stagger(t0,i,n,step,total){var s=step==null?DUR.stagger:step;if(total!=null&&n>1)s=Math.min(s,total/(n-1));return t0+i*s;}
  /* wave / saw: periodic motion for states that last (waiting); never decorative constant motion */
  function wave(t,amp,freq,phase){return amp*Math.sin(2*Math.PI*freq*t+(phase||0));}
  function saw(t,period){return ((t%period)+period)%period/period;}
  /* mix: colour between two #rrggbb values */
  function mix(a,b,u){u=clamp(u);var p=function(h,i){return parseInt(h.slice(1+2*i,3+2*i),16);},o='#';
    for(var i=0;i<3;i++){var v=Math.round(p(a,i)+(p(b,i)-p(a,i))*u);o+=(v<16?'0':'')+v.toString(16);}return o;}
  /* tag: mark the first circle of an svg string as token `id` (rings, dots drawn by other helpers) */
  function tag(svg,id){return svg.replace('<circle ','<circle data-token="'+esc(id)+'" ');}
  /* follow: a marker that rides on the data (a line's head); it may jump when the data jumps, so the
     speed limit does not apply - the data, not the animation, sets its pace */
  function follow(svg){return svg.replace('<circle ','<circle data-follow="1" ');}
  function ease(T,t0,dur){return tween(T,t0,dur||M.fade,'inOut');}
  return {CURVE:CURVE,DUR:DUR,tween:tween,spring:spring,pop:pop,approach:approach,stagger:stagger,wave:wave,saw:saw,mix:mix,M:M,ortho:ortho,wire:wire,plen:plen,at:at,token:token,tag:tag,follow:follow,ease:ease,C:C,PILL:PILL,f:f,clamp:clamp,esc:esc,text:text,rich:rich,tw:tw,rect:rect,pill:pill,line:line,dot:dot,ring:ring,path:path,arrow:arrow,gauge:gauge,num:num,grp:grp};
})();
var CA_GRAMMARS={},CA_SCENES={};
