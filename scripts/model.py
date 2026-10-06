"""Small deterministic helpers shared by every visual: input checks, sample statistics, caption pacing (reading
time and the playback-rate map), axis ceilings, piecewise-linear series and token streams. Pure Python, no I/O."""
from __future__ import annotations
import math


def finite(v,name,lo=0,hi=1e6):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
        raise ValueError(f'{name}: finite number in [{lo},{hi}] required')
    return v

def percentile(values,counts,q):
    if len(values)!=len(counts) or not 1<=len(values)<=30 or values!=sorted(set(values)):
        raise ValueError('Expected equal-length sorted unique values/frequencies')
    for v in values:finite(v,'value')
    for n in counts:
        finite(n,'count',0,1000)
        if n!=int(n):raise ValueError('Counts must be integer')
    total=sum(counts)
    if not total:raise ValueError('Empty distribution')
    rank=math.ceil(q*total);running=0
    for value,n in zip(values,counts):
        running+=n
        if running>=rank:return value
    raise AssertionError('unreachable')

def stats(values,counts):
    p={f'p{int(q*100)}':percentile(values,counts,q) for q in [.5,.95,.99]}
    p.update(n=sum(counts),mean=sum(v*n for v,n in zip(values,counts))/sum(counts));return p

CAPTION_CPS=12.0      # reading speed assumed for Korean captions (chars per second)
CAPTION_MIN_S=2.5     # minimum wall seconds any caption stays on screen
CAPTION_MAX_CHARS=50  # longer captions are a writing problem, not a pacing problem
DEFAULT_SPEED=1.25

def caption_need(text):return max(CAPTION_MIN_S,len(text)/CAPTION_CPS)

def rate_at(rate,t):
    r=1
    for x in rate:
        if t>=x[0]-1e-9:r=x[1]
    return r

def caption_walls(captions,rate,end,speed=DEFAULT_SPEED):
    """Wall seconds each caption is on screen during one play (last caption: until the end)."""
    caps=sorted(captions,key=lambda c:c[0]);pts=sorted({0.0,end}|{x[0] for x in rate if 0<=x[0]<=end}|{c[0] for c in caps});out=[]
    for i,c in enumerate(caps):
        a=c[0];b=caps[i+1][0] if i+1<len(caps) else end
        out.append(sum((y-x)/(rate_at(rate,x)*speed) for x,y in zip(pts,pts[1:]) if x>=a-1e-9 and y<=b+1e-9))
    return out

def paced_rate(captions,end,base,speed=DEFAULT_SPEED,floor=0.12):
    """Playback-rate map: `base` (model-time pacing) slowed wherever a caption would otherwise
    disappear before it can be read. Raises when captions are too close to be read at all."""
    caps=sorted(captions,key=lambda c:c[0])
    for c in caps:
        if len(c[2])>CAPTION_MAX_CHARS:raise ValueError(f'Caption longer than {CAPTION_MAX_CHARS} chars: {c[2]}')
    pts=sorted({0.0,end}|{x[0] for x in base if 0<=x[0]<=end}|{c[0] for c in caps});out=[]
    for i,c in enumerate(caps):
        a=c[0];b=caps[i+1][0] if i+1<len(caps) else end
        segs=[(x,y,rate_at(base,x)) for x,y in zip(pts,pts[1:]) if x>=a-1e-9 and y<=b+1e-9]
        need=caption_need(c[2]) if i+1<len(caps) else 0
        wall=sum((y-x)/(r*speed) for x,y,r in segs)
        if need and wall<=1e-9:raise ValueError(f'Caption {c[1]} has no time on screen; merge it with the next one')
        k=1 if wall>=need else wall/need
        for x,y,r in segs:
            if r*k<floor:raise ValueError(f'Caption {c[1]} needs a playback rate below {floor}; merge or move captions')
            out.append([round(x,4),math.floor(r*k*1e4)/1e4])   # round down: never shorter than needed
    merged=[]
    for x in out:
        if not merged or abs(merged[-1][1]-x[1])>1e-9:merged.append(x)
    return merged

def nice_max(v):
    """Smallest 1/1.2/1.5/2/2.5/3/4/5/6/8 x 10^k that is >= v (axis ceilings)."""
    if v<=0:return 1
    e=10**math.floor(math.log10(v))
    return next(m*e for m in (1,1.2,1.5,2,2.5,3,4,5,6,8,10) if m*e>=v-1e-9)

def grp(v):return f'{round(v):,}'

def interp(ts,vs,t):
    if t<=ts[0]:return vs[0]
    for i in range(1,len(ts)):
        if t<=ts[i]:
            span=ts[i]-ts[i-1] or 1;return vs[i-1]+(vs[i]-vs[i-1])*(t-ts[i-1])/span
    return vs[-1]

def first_reach(ts,vs,level):
    """First time a non-decreasing piecewise-linear series reaches level, or None."""
    if vs[0]>=level-1e-9:return ts[0]
    for i in range(1,len(ts)):
        if vs[i]>=level-1e-9:
            span=vs[i]-vs[i-1];return ts[i] if span<=0 else ts[i-1]+(ts[i]-ts[i-1])*(level-vs[i-1])/span
    return None

def token_unit(rate,most=30):
    """Requests per drawn token, so the busiest stream draws at most `most` tokens/s."""
    return next(u for u in (1,2,5,10,20,50,100,200,500,1000,2000,5000,10000) if rate/u<=most+1e-9)

def fluid_tokens(series,unit):
    """Each token = `unit` requests: arrival when cumulative inflow crosses k*unit; a token is
    rejected when accepted inflow has not grown by a further unit; an accepted token leaves
    the queue (FIFO) when cumulative service crosses its accepted index * unit."""
    ts,inc,srv,rej=series['t'],series['inc'],series['srv'],series['rej'];out=[];accepted=0;k=1
    while k*unit<=inc[-1]+1e-9:
        ta=first_reach(ts,inc,k*unit);acc=interp(ts,inc,ta)-interp(ts,rej,ta)
        if math.floor(acc/unit+1e-6)<accepted+1:out.append([round(ta,4),None,1])
        else:
            accepted+=1;tsv=first_reach(ts,srv,accepted*unit)
            out.append([round(ta,4),None if tsv is None else round(max(ta,tsv),4),0])
        k+=1
    return out

TOKEN_WALL_MAX = 450   # px per wall second, under the gate's 480 (visual_gates.MOTION_MAX) at any build speed


def token_speed(peak_rate,unit,rate=None,spacing=15):
    """Token speed in px per model second: tokens of the busiest stream sit ~`spacing` px apart, but on
    screen (playback rate map x the fastest build speed, 1.5x) no faster than TOKEN_WALL_MAX - a busier
    or fast-forwarded stream packs its tokens closer instead of moving them faster."""
    fastest=max([r for _,r in (rate or [[0,1]])])*1.5
    return round(min(TOKEN_WALL_MAX/fastest,max(240,spacing*peak_rate/unit)))
