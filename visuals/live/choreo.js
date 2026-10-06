/* Choreography evaluator (docs/design/motion-concept-architecture.md, L2). Cues are resolved and
   validated in Python (scripts/choreo.py) and arrive as [target, prop, t0, dur, curve, from, to].
   Pure in T like everything else: v() gives the value of a property at T, since() when its last
   change started. A target/property with no cue keeps the scene's own default. */
var CA_CHOREO=function(cues,K){var idx={};(cues||[]).forEach(function(c){var k=c[0]+'|'+c[1];(idx[k]=idx[k]||[]).push(c);});
  for(var k in idx)idx[k].sort(function(a,b){return a[2]-b[2];});
  return {
    v:function(target,prop,T,def){var L=idx[target+'|'+prop];if(!L)return def;var val=L[0][5];
      for(var i=0;i<L.length;i++){var c=L[i];if(T<c[2])break;var u=c[3]>0?K.clamp((T-c[2])/c[3]):1;val=c[5]+(c[6]-c[5])*K.CURVE[c[4]](u);}return val;},
    since:function(target,prop,T){var L=idx[target+'|'+prop],s=null;if(L)L.forEach(function(c){if(T>=c[2])s=c[2];});return s;},
    has:function(){return Object.keys(idx).length>0;}};
};
