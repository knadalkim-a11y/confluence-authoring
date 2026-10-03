/* Grammar: panels that share one model-time axis, revealed up to T.
   Annotations are drawn only by callers that pass a time at which they become true. */
CA_GRAMMARS.timePanels={
  panel:function(g,y,h,end,ymax){var p={x0:g.nw?30:34,x1:g.W-4,y:y,h:h,end:end,ymax:ymax};
    p.X=function(t){return p.x0+(p.x1-p.x0)*t/p.end;};p.Y=function(v){return p.y+p.h-p.h*v/p.ymax;};return p;},
  band:function(K,a,b,t0,t1,label){return K.rect(a.X(t0),a.y,a.X(t1)-a.X(t0),b.y+b.h-a.y,{r:0,fill:K.C.band})+K.text(a.X(t0)+5,a.y+13,label,{fs:11,c:K.C.amber});},
  title:function(K,p,label,legend){var o=K.text(0,p.y-10,label,{fs:12,c:K.C.ink,w:700}),x=p.x1;
    (legend||[]).slice().reverse().forEach(function(l){var w=l[0].length*11+16;x-=w;o+=K.rect(x,p.y-19,9,9,{r:2,fill:l[1],op:.75})+K.text(x+13,p.y-11,l[0],{fs:11});x-=8;});return o;},
  yTicks:function(K,p,ticks,grid){var o=K.line(p.x0,p.y+p.h,p.x1,p.y+p.h,K.C.edge);
    ticks.forEach(function(t){o+=K.text(p.x0-6,p.Y(t[0])+4,t[1],{fs:11,a:'end',c:t[2]||K.C.faint});if(grid&&t[0])o+=K.line(p.x0,p.Y(t[0]),p.x1,p.Y(t[0]),K.C.rule);});return o;},
  /* lower/upper: sampled series at dt; drawn up to sample n. */
  stacked:function(K,p,dt,n,lower,upper,cl,cu){if(n<1)return '';var i,a='M'+K.f(p.X(0))+' '+K.f(p.Y(0)),rim=[],q;
    for(i=0;i<=n;i++){a+='L'+K.f(p.X(i*dt))+' '+K.f(p.Y(lower[i]));rim.push(K.f(p.X(i*dt))+' '+K.f(p.Y(lower[i]+upper[i])));}
    a+='L'+K.f(p.X(n*dt))+' '+K.f(p.Y(0))+'Z';q='M'+rim.join('L');for(i=n;i>=0;i--)q+='L'+K.f(p.X(i*dt))+' '+K.f(p.Y(lower[i]));
    return K.path(a,cl,'.72')+K.path(q+'Z',cu,'.72');},
  limit:function(K,p,v,label){return K.line(p.x0,p.Y(v),p.x1,p.Y(v),K.C.red,{d:'4 3',op:.8})+K.text(p.x1,p.Y(v)-4,label,{fs:11,c:K.C.red,a:'end'});},
  xAxis:function(K,p,step,unit){var o='',t;for(t=0;t<=p.end+1e-9;t+=step)o+=K.text(p.X(t),p.y+p.h+15,K.f(t)+(t+step>p.end+1e-9?unit:''),{fs:11,c:K.C.faint,a:'middle'});return o;},
  cursor:function(K,a,b,T){return T<a.end-1e-6?K.line(a.X(T),a.y-2,a.X(T),b.y+b.h,K.C.ink,{op:.28}):'';}
};
/* Panel inside a horizontal box (columns); series on explicit time arrays, cut at T. */
CA_GRAMMARS.timePanels.panelIn=function(x0,x1,y,h,end,ymax){var p={x0:x0,x1:x1,y:y,h:h,end:end,ymax:ymax};
  p.X=function(t){return p.x0+(p.x1-p.x0)*t/p.end;};p.Y=function(v){return p.y+p.h-p.h*Math.min(v,p.ymax)/p.ymax;};return p;};
CA_GRAMMARS.timePanels.at=function(ts,vs,T){if(T<=ts[0])return vs[0];for(var i=1;i<ts.length;i++)if(T<=ts[i]){var r=(T-ts[i-1])/(ts[i]-ts[i-1]||1);return vs[i-1]+(vs[i]-vs[i-1])*r;}return vs[vs.length-1];};
CA_GRAMMARS.timePanels.cut=function(K,p,ts,vs,T){var pts=[],i;for(i=0;i<ts.length&&ts[i]<=T+1e-9;i++)pts.push(K.f(p.X(ts[i]))+' '+K.f(p.Y(vs[i])));
  if(i<ts.length&&i>0)pts.push(K.f(p.X(T))+' '+K.f(p.Y(CA_GRAMMARS.timePanels.at(ts,vs,T))));return pts;};
CA_GRAMMARS.timePanels.area=function(K,p,ts,vs,T,color){var pts=this.cut(K,p,ts,vs,T);if(pts.length<2)return '';
  var last=Math.min(T,ts[ts.length-1]);return K.path('M'+K.f(p.X(ts[0]))+' '+K.f(p.Y(0))+'L'+pts.join('L')+'L'+K.f(p.X(last))+' '+K.f(p.Y(0))+'Z',color,'.72');};
CA_GRAMMARS.timePanels.series=function(K,p,ts,vs,T,color,sw){var pts=this.cut(K,p,ts,vs,T);if(pts.length<2)return '';
  return '<path d="M'+pts.join('L')+'" fill="none" stroke="'+color+'" stroke-width="'+(sw||2)+'" stroke-linejoin="round"/>';};
CA_GRAMMARS.timePanels.mark=function(K,a,b,t,label,c){return K.line(a.X(t),a.y,a.X(t),b.y+b.h,c||K.C.red,{d:'4 3',op:.7})+(label?K.text(a.X(t)+4,a.y+12,label,{fs:11,c:c||K.C.red}):'');};
CA_GRAMMARS.timePanels.ticksX=function(K,p,ticks){return ticks.map(function(t){return K.text(p.X(t[0]),p.y+p.h+15,t[1],{fs:11,c:K.C.faint,a:t[0]<=0?'start':t[0]>=p.end?'end':'middle'});}).join('');};
