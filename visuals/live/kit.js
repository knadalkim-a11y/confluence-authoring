/* SVG string helpers shared by live grammars. Pure functions: no DOM access, so the
   same code renders the animated view in the browser and the static fallback in Node. */
var CA_KIT=(function(){
  var C={ink:'#1d2733',muted:'#66727f',faint:'#a3acb7',rule:'#e2e7ed',edge:'#cfd6df',rail:'#c9d1db',
    blue:'#2c6ad8',blueSoft:'#dfe9fb',red:'#cf3d29',redSoft:'#fbe4e0',redRail:'#e9b3aa',
    amber:'#c97f0a',amberSoft:'#f9e3b9',band:'#fff7ea',green:'#2f9a5a',purple:'#7b55b5',paper:'#fff',paper2:'#fafbfc',hotPaper:'#fff8f6'};
  function f(v){return Math.round(v*10)/10;}
  function clamp(v){return v<0?0:v>1?1:v;}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function text(x,y,s,o){o=o||{};return '<text x="'+f(x)+'" y="'+f(y)+'" font-size="'+(o.fs||12)+'" fill="'+(o.c||C.muted)+'"'+
    (o.a?' text-anchor="'+o.a+'"':'')+(o.w?' font-weight="'+o.w+'"':'')+'>'+esc(s)+'</text>';}
  function rect(x,y,w,h,o){o=o||{};return '<rect x="'+f(x)+'" y="'+f(y)+'" width="'+f(Math.max(0,w))+'" height="'+f(Math.max(0,h))+
    '" rx="'+(o.r==null?4:o.r)+'" fill="'+(o.fill||'none')+'"'+(o.st?' stroke="'+o.st+'" stroke-width="'+(o.sw||1)+'"':'')+
    (o.op!=null?' opacity="'+f(o.op*100)/100+'"':'')+'/>';}
  function line(x1,y1,x2,y2,c,o){o=o||{};return '<line x1="'+f(x1)+'" y1="'+f(y1)+'" x2="'+f(x2)+'" y2="'+f(y2)+'" stroke="'+c+
    '" stroke-width="'+(o.sw||1)+'"'+(o.d?' stroke-dasharray="'+o.d+'"':'')+(o.op!=null?' opacity="'+o.op+'"':'')+'/>';}
  function dot(x,y,r,c,op){return '<circle cx="'+f(x)+'" cy="'+f(y)+'" r="'+r+'" fill="'+c+'"'+(op!=null&&op<1?' opacity="'+f(op*100)/100+'"':'')+'/>';}
  function path(d,fill,op){return '<path d="'+d+'" fill="'+fill+'"'+(op!=null?' opacity="'+op+'"':'')+'/>';}
  function num(v,d){return Number(v).toFixed(d==null?1:d);}
  /* Integer with thousands separators, locale independent. */
  function grp(v){var n=Math.round(v),s=String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g,',');return (n<0?'-':'')+s;}
  return {C:C,f:f,clamp:clamp,esc:esc,text:text,rect:rect,line:line,dot:dot,path:path,num:num,grp:grp};
})();
var CA_GRAMMARS={},CA_SCENES={};
