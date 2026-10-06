"""Shared, offline reference primitives; uses the existing v0.2 player unchanged.

Charts use explicit time coordinates rather than stroke length. Display geometry,
markers and tables come from the same values. Only this module inserts raw markup;
external text is escaped. There is no runtime JS in a generated macro.
"""
from __future__ import annotations
import html, math, re, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COLORS=['#326cce','#ac3c51','#875aaf','#287959','#ab711f']
def esc(value): return html.escape(str(value),quote=True)
def fmt(value):
    if isinstance(value,str): return value
    return f'{value:,.2f}'.rstrip('0').rstrip('.') if value!=int(value) else f'{value:,.0f}'
def sub(source,values):
    names=set(re.findall(r'{{([A-Z][A-Z0-9_]*)}}',source))
    missing=names-values.keys()
    if missing: raise ValueError('Missing slots: '+','.join(sorted(missing)))
    return re.sub(r'{{([A-Z][A-Z0-9_]*)}}',lambda m:values[m[1]],source)
def lerp(a,b,t): return a+(b-a)*t
def clamp(x): return max(0,min(1,x))
def piece(t,points):
    if t<=points[0][0]:return points[0][1]
    for (a,av),(b,bv) in zip(points,points[1:]):
        if t<=b:return lerp(av,bv,(t-a)/(b-a))
    return points[-1][1]
def samples(fn,n=81): return [[i/(n-1),round(fn(i/(n-1)),6)] for i in range(n)]

def simplify_track(frames,tolerance=0.00012):
    """Remove collinear CSS keyframes, not samples from source tables/geometry.

    Same property/unit skeleton and per-value linear equivalence are required.
    This is a rendering byte optimization, not temporal smoothing of source data.
    """
    numeric=re.compile(r"[-+]?(?:\d*\.\d+|\d+)")
    def parse(value):
        return numeric.sub("#",value),[float(m[0]) for m in numeric.finditer(value)]
    out=[]
    for current in frames:
        out.append(current)
        while len(out)>=3:
            a,b,c=out[-3:];ka,va=parse(a[1]);kb,vb=parse(b[1]);kc,vc=parse(c[1])
            if ka!=kb or kb!=kc or len(va)!=len(vb) or len(vb)!=len(vc):break
            if '#' in a[1] and not a[1]==b[1]==c[1]:break
            ratio=(b[0]-a[0])/(c[0]-a[0])
            if not all(abs(y-(x+(z-x)*ratio))<=tolerance for x,y,z in zip(va,vb,vc)):break
            if not va and not a[1]==b[1]==c[1]:break
            del out[-2]
    return out

class ReferenceScene:
    def __init__(self,prefix=None):
        self.prefix=prefix or 'ca-'+uuid.uuid4().hex[:12]
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,40}',self.prefix):raise ValueError('Invalid prefix')
        self.rules=[]; self.tables=[]; self.serial=0; self.numeric={}
    def uid(self,kind='node'):
        self.serial+=1;return f'{self.prefix}-{kind}-{self.serial}'
    def anim(self,frames,final):
        name=self.uid('track');cls=name+'-shape'
        self.rules.append(f'.{self.prefix} .{cls}{{--a:{name}-a;--b:{name}-b;{final}}}\n@keyframes {name}-a{{{frames}}}\n@keyframes {name}-b{{{frames}}}')
        return 'ca-anim '+cls
    def track(self,frames):
        # Input times are normalized explanation time; run window = 6..86%.
        if not frames:raise ValueError('Empty track')
        if any(not 0<=t<=1 for t,_ in frames) or any(a[0]>=b[0] for a,b in zip(frames,frames[1:])):
            raise ValueError('Track times must strictly increase in [0,1]')
        frames=simplify_track(frames)
        first=frames[0][1];last=frames[-1][1]
        css='0%{'+first+'}'+''.join(f'{6+80*t:.5f}%{{{value}}}' for t,value in frames)+'100%{'+last+'}'
        return self.anim(css,last)
    def reveal(self,at=0.6):
        at=clamp(at);end=min(1,at+.04)
        if at==1:return self.track([(0,'opacity:0'),(1,'opacity:1')])
        frames=[(0,'opacity:0')]
        if at>0:frames.append((at,'opacity:0'))
        frames.append((end,'opacity:1'))
        if end<1:frames.append((1,'opacity:1'))
        return self.track(frames)
    def pulse(self,start,end):
        times=sorted(set([0,start,min(start+.02,end),max(start,end-.02),end,1]))
        return self.track([(t,f'opacity:{1 if start<t<end else 0}') for t in times])
    def table(self,title,headers,rows):
        self.tables.append('<details><summary>'+esc(title)+'</summary><div class="mr-table"><table><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(fmt(v) if isinstance(v,(int,float)) else v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div></details>')
    def svg(self,content,label,height=220):
        uid=self.uid('svg-title')
        return f'<svg class="mr-svg" viewBox="0 0 500 {height}" role="img" aria-labelledby="{uid}"><title id="{uid}">{esc(label)}</title>{content}</svg>'
    def panel(self,title,body,unit='',summary=''):
        return '<div class="mr-panel"><h4>'+esc(title)+'</h4><p class="mr-unit">'+esc(unit)+'</p>'+body+('<p class="mr-summary">'+esc(summary)+'</p>' if summary else '')+'</div>'
    def grid(self,*panels):return '<div class="mr-grid">'+''.join(panels)+'</div>'
    def stack(self,*panels):return '<div class="mr-stack">'+''.join(panels)+'</div>'
    def metrics(self,entries):
        return '<div class="mr-metric-row">'+''.join('<div class="mr-metric"><span>'+esc(k)+'</span><b>'+esc(v)+'</b><span>'+esc(note)+'</span></div>' for k,v,note in entries)+'</div>'
    def chart(self,title,curves,unit='',maximum=None,events=(),x_label='관찰 시간',x_end='끝',threshold=None,x_ticks=None):
        # curve: (label, [[normalized x,value],...], color)
        allvals=[]
        for label,seq,color in curves:
            if len(seq)<2:raise ValueError('Curve needs >=2 observations')
            for x,y in seq:
                if not isinstance(x,(float,int)) or not isinstance(y,(float,int)) or not math.isfinite(x+y) or not 0<=x<=1:raise ValueError('Invalid chart point')
                allvals.append(y)
        maximum=maximum if maximum is not None else max(1,max(allvals))*1.15
        if not math.isfinite(maximum) or maximum<=0 or min(allvals)<0 or max(allvals)>maximum+1e-6:raise ValueError('Invalid y range')
        x0=55;xw=420;yb=180;yh=135
        X=lambda x:x0+x*xw;Y=lambda y:yb-y/maximum*yh
        grid=''.join(f'<line x1="55" y1="{Y(v):.3f}" x2="475" y2="{Y(v):.3f}" stroke="#dce6f0"/><text x="46" y="{Y(v)+5:.3f}" text-anchor="end">{esc(fmt(v))}</text>' for v in [0,maximum/2,maximum])
        extent=max(seq[-1][0] for _,seq,_ in curves)
        stop=[(0,'width:0px'),(extent,f'width:{420*extent}px')]
        if extent<1:stop.append((1,f'width:{420*extent}px'))
        clip=self.uid('clip');grow=self.track(stop)
        body=f'<defs><clipPath id="{clip}" clipPathUnits="userSpaceOnUse"><rect x="55" y="35" width="420" height="150" class="{grow}"/></clipPath></defs>'+grid
        if threshold is not None:
            if not 0<=threshold<=maximum:raise ValueError('Threshold outside chart')
            body+=f'<line x1="55" x2="475" y1="{Y(threshold)}" y2="{Y(threshold)}" stroke="#ae7541" stroke-dasharray="6 4"/><text x="470" y="{Y(threshold)-6}" text-anchor="end">기준 {esc(fmt(threshold))}</text>'
        for label,seq,color in curves:
            d=' '.join(('M' if i==0 else 'L')+f'{X(x):.3f},{Y(y):.3f}' for i,(x,y) in enumerate(seq))
            body+=f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.8" stroke-linejoin="round" clip-path="url(#{clip})"/>'
            dot=self.track([(x,f'transform:translate({X(x):.4f}px,{Y(y):.4f}px)') for x,y in seq])
            body+=f'<circle data-mr-dot="{esc(label)}" class="{dot}" r="4" cx="0" cy="0" fill="{color}" stroke="#fff" stroke-width="1.3"/>'
            self.table(title+' · '+label,['정규화 x (0..1)',unit or '값'],seq)
        cursor=self.track([(0,'transform:translateX(0px)'),(extent,f'transform:translateX({420*extent}px)')]+([] if extent==1 else [(1,f'transform:translateX({420*extent}px)')]))
        body+=f'<line data-mr-clock="true" class="{cursor}" x1="55" x2="55" y1="35" y2="180" stroke="#97aac0" stroke-dasharray="3 4"/>'
        for i,(at,label,color) in enumerate(events):
            cls=self.reveal(at)
            anchor='end' if at>.7 else 'start';dx=-5 if at>.7 else 5
            body+=f'<g data-mr-marker="{esc(label)}" class="{cls}"><line x1="{X(at)}" x2="{X(at)}" y1="37" y2="180" stroke="{color}" stroke-dasharray="4 4"/><text x="{X(at)+dx}" y="{17+(i%2)*17}" text-anchor="{anchor}" style="fill:{color}">{esc(label)}</text></g>'
        ticks=x_ticks or [(0,'시작'),(.5,''),(1,x_end)]
        body+=''.join(f'<text x="{X(at)}" y="207" text-anchor="'+('start' if at==0 else 'end' if at==1 else 'middle')+'">'+esc(label)+'</text>' for at,label in ticks)
        summary=' · '.join(label+': '+fmt(seq[0][1])+' → '+fmt(seq[-1][1])+' '+unit for label,seq,color in curves)
        legend='<div class="mr-legend">'+''.join('<span><i style="background:'+color+'"></i>'+esc(label)+'</span>' for label,seq,color in curves)+'</div>' if len(curves)>1 else ''
        return self.panel(title,self.svg(body,title)+legend,unit+' · '+x_label,summary)
    def phases(self,texts):
        result='<div class="mr-phases" aria-hidden="true">'
        for i,(at,title,message) in enumerate(texts):
            end=texts[i+1][0] if i+1<len(texts) else 1.1
            if i==len(texts)-1:cls=self.reveal(at)
            elif i==0:cls=self.track([(0,'opacity:1'),(max(0,end-.015),'opacity:1'),(end,'opacity:0'),(1,'opacity:0')])
            else:cls=self.pulse(at,end)
            result+=f'<div class="mr-phase {cls}"><b>{i+1:02d} / {len(texts):02d} · {esc(title)}</b>{esc(message)}</div>'
        progress=self.track([(0,'transform:scaleX(0)'),(1,'transform:scaleX(1)')])
        return result+'</div><div class="mr-progress" aria-hidden="true"><i class="'+progress+'"></i></div>'
    def box(self,x,y,w,h,label,detail='',color='#326cce',state=None):
        cls='' if state is None else ' class="'+state+'"'
        return f'<g{cls}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#f7faff" stroke="{color}" stroke-width="1.5"/><text class="mr-label" x="{x+w/2}" y="{y+h/2-5 if detail else y+h/2+6}" text-anchor="middle">{esc(label)}</text>'+ (f'<text x="{x+w/2}" y="{y+h/2+18}" text-anchor="middle">{esc(detail)}</text>' if detail else '')+'</g>'
    def packet(self,points,color='#326cce',r=4):
        # tuples (time,x,y,opacity); all positions symbolic, never asserted packet counts.
        cls=self.track([(t,f'transform:translate({x:.3f}px,{y:.3f}px);opacity:{alpha}') for t,x,y,alpha in points])
        return f'<circle class="{cls}" cx="0" cy="0" r="{r}" fill="{color}"/>'
    def token_stream(self,x1,y1,x2,y2,start=0,end=1,count=10,color='#326cce'):
        out=''
        for i in range(count):
            t=start+(end-start)*i/max(1,count);finish=min(1,t+.11)
            seq=[(0,x1,y1,0)]
            if t>0:seq.append((t,x1,y1,0))
            seq.extend([(min(t+.003,finish-.002),x1,y1,1),(finish-.001,x2,y2,1),(finish,x2,y2,0)])
            if finish<1:seq.append((1,x2,y2,0))
            out+=self.packet(seq,color)
        return out

def assemble(scene,meta,content,phases,duration=18):
    if not 8<=duration<=30:raise ValueError('Duration must be 8..30 seconds')
    p=scene.prefix
    body=sub((ROOT/'visuals/motion/monitoring-reference.html').read_text(),{'CONTENT':content,'PHASES':scene.phases(phases)})
    css=sub((ROOT/'visuals/components/player.css').read_text(),{'PREFIX':p,'DURATION':str(duration),'REPEAT':'1'})
    css=css.rstrip()+'\n\n'  # stable boundary independent of trailing newlines
    css+=sub((ROOT/'visuals/components/monitoring.css').read_text(),{'PREFIX':p})
    vals={'PREFIX':p,'PATTERN':'reference-'+meta['id'],'CSS':css,'ANIMATION_CSS':'\n'.join(scene.rules),'SCENE':body,'DURATION':str(duration),'MODE_LABEL':'설명용 합성 시나리오','DATA_TABLE':''.join(scene.tables),'TITLE':esc(meta['title']),'DESCRIPTION':esc(meta['goal']),'CAPTION':esc(meta['conclusion']),'PROVENANCE':esc(meta['assumptions'])}
    return sub((ROOT/'visuals/components/player.html').read_text(),vals)

from live_scene import document   # one page wrapper for every preview (shared with the spec path)
