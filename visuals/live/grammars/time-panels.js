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
