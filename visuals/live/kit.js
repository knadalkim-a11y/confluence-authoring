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
  var PILL={ok:['#d3f9d8','#237032'],warn:['#fff3bf','#a85a00'],hot:['#e03131','#fff'],info:['#e7f5ff','#1864ab']};
  function f(v){return Math.round(v*10)/10;}
  function clamp(v){return v<0?0:v>1?1:v;}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  /* halo: white outline under the glyphs, for labels placed over lines, areas or dots. */
  function halo(o){return o.halo?' stroke="#fff" stroke-width="3" stroke-linejoin="round" paint-order="stroke"':'';}
  function text(x,y,s,o){o=o||{};return '<text x="'+f(x)+'" y="'+f(y)+'" font-size="'+(o.fs||12)+'" fill="'+(o.c||C.muted)+'"'+
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
    if(!o.noLabel)s+=text(x+w/2,y+21,Math.round(fr*100)+'%',{fs:12,c:hot?C.redText:C.greenText,a:'middle',w:700});return s;}
  function num(v,d){return Number(v).toFixed(d==null?1:d);}
  /* Integer with thousands separators, locale independent. */
  function grp(v){var n=Math.round(v),s=String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g,',');return (n<0?'-':'')+s;}
  return {C:C,PILL:PILL,f:f,clamp:clamp,esc:esc,text:text,rich:rich,tw:tw,rect:rect,pill:pill,line:line,dot:dot,ring:ring,path:path,arrow:arrow,gauge:gauge,num:num,grp:grp};
})();
var CA_GRAMMARS={},CA_SCENES={};
