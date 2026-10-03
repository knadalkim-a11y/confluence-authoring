/* Live runtime v1: clock, playback-rate map, controls, reduced motion, visibility,
   resize, print. Plays once and keeps the final scene; replay is user controlled.
   Starts from the server-rendered static final scene, so no-JS/export keeps content. */
(function(root,D){
  if(!root||root.getAttribute('data-ca-live-bound'))return;root.setAttribute('data-ca-live-bound','1');
  var K=CA_KIT,sc=CA_SCENES[D.scene](D,K,CA_GRAMMARS),svg=root.querySelector('svg[data-ca-live]'),
      statsEl=root.querySelector('[data-ca-stats]'),cap=root.querySelector('[data-ca-caption]'),btn=root.querySelector('[data-a="play"]');
  var speed=Number(root.getAttribute('data-ca-speed'))||1,T=sc.end,playing=false,started=false,visible=true,last=null,g=null,lastCap=-1;
  function rate(t){var r=1;D.rate.forEach(function(x){if(t>=x[0]-1e-9)r=x[1];});return r*speed;}
  function capAt(t){var j=0;D.captions.forEach(function(c,i){if(t>=c[0]-1e-9)j=i;});return j;}
  function b(v,hot){return '<b'+(hot?' class="hot"':'')+'>'+K.esc(v)+'</b>';}
  function render(){svg.innerHTML=sc.draw(T,g);var s=sc.stats(T),h='<span class="grp">';
    s.left.forEach(function(x){h+='<span>'+K.esc(x[0])+b(x[1],x[3])+K.esc(x[2])+'</span>';});
    h+='</span><span>'+K.esc(s.right[0])+b(s.right[1],s.right[4])+K.esc(s.right[2])+b(s.right[3],s.right[4])+'</span>';statsEl.innerHTML=h;
    var c=capAt(T);if(c!==lastCap){lastCap=c;cap.innerHTML='<span class="n">'+K.esc(D.captions[c][1])+'</span>'+K.esc(D.captions[c][2]);}
    root.setAttribute('data-ca-t',T.toFixed(3));}
  function layout(){var W=Math.max(300,Math.round(svg.getBoundingClientRect().width||root.clientWidth));if(g&&g.W===W)return;
    g=sc.geom(W);svg.setAttribute('viewBox','0 0 '+W+' '+g.H);render();}
  function setPlaying(p){playing=p;btn.textContent=p?'일시정지':'재생';btn.setAttribute('aria-pressed',String(!p));}
  function tick(ts){if(last==null)last=ts;var dt=Math.min(.05,(ts-last)/1000);last=ts;
    if(playing&&visible){T=Math.min(sc.end,T+dt*rate(T));render();if(T>=sc.end)setPlaying(false);}
    if(playing)requestAnimationFrame(tick);else last=null;}
  function play(from){if(from!=null)T=from;setPlaying(true);last=null;requestAnimationFrame(tick);}
  root.querySelector('[data-ca-controls]').addEventListener('click',function(ev){var a=ev.target.getAttribute&&ev.target.getAttribute('data-a');if(!a)return;
    if(a==='play'){if(playing)setPlaying(false);else play(T>=sc.end?0:null);}
    if(a==='restart')play(0);
    if(a==='end'){setPlaying(false);T=sc.end;render();}});
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  window.addEventListener('beforeprint',function(){setPlaying(false);T=sc.end;render();});
  if('ResizeObserver' in window)new ResizeObserver(layout).observe(root);
  root.__caLive={seek:function(t){setPlaying(false);T=Math.max(0,Math.min(sc.end,t));render();},state:function(){var s=sc.state(T);return {T:T,used:s.n,queued:s.qd.length,playing:playing};},end:sc.end};
  layout();setPlaying(false);
  if(reduce)return;
  function start(){if(!started){started=true;play(0);}}
  if('IntersectionObserver' in window)new IntersectionObserver(function(es){visible=es[0].isIntersecting;if(visible)start();last=null;},{threshold:.25}).observe(root);
  else start();
})(document.querySelector('[data-ca-prefix="%%PREFIX%%"]'),%%DATA%%);
