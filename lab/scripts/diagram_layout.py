"""Small, explicit layouts. One polyline is shared by the rail and motion path.

No automatic graph engine: these six layouts cover three existing reference cases.
Ports are on node boundaries; shared trunks are explicitly named and drawn once.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math

Point = tuple[float, float]

def path_d(points: tuple[Point, ...] | list[Point]) -> str:
    if len(points) < 2:
        raise ValueError('A route needs at least two points')
    if any(not math.isfinite(v) for p in points for v in p):
        raise ValueError('Nonfinite route coordinate')
    return ' '.join(('M' if i == 0 else 'L') + f'{x:g},{y:g}' for i,(x,y) in enumerate(points))

@dataclass(frozen=True)
class Node:
    key: str
    x: float
    y: float
    w: float
    h: float
    shape: str = 'rect'
    def port(self, side: str) -> Point:
        if side not in ('left','right','top','bottom'):
            raise ValueError('Unknown port side')
        return {'left':(self.x,self.y+self.h/2), 'right':(self.x+self.w,self.y+self.h/2),
                'top':(self.x+self.w/2,self.y), 'bottom':(self.x+self.w/2,self.y+self.h)}[side]
    @property
    def box(self): return self.x,self.y,self.w,self.h

@dataclass(frozen=True)
class Route:
    key: str
    points: tuple[Point, ...]
    source: tuple[str,str] | None = None
    target: tuple[str,str] | None = None
    parts: tuple[str, ...] = ()  # semantic shared bus, drawn once as these parts
    kind: str = 'external'
    @property
    def d(self): return path_d(self.points)
    @property
    def length(self): return sum(math.dist(a,b) for a,b in zip(self.points,self.points[1:]))
    def at(self, fraction: float) -> Point:
        remaining=max(0,min(1,fraction))*self.length
        for a,b in zip(self.points,self.points[1:]):
            length=math.dist(a,b)
            if remaining <= length:
                f=remaining/length if length else 0
                return a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f
            remaining-=length
        return self.points[-1]

@dataclass
class Layout:
    case: str
    variant: str
    width: int
    height: int
    nodes: dict[str, Node]
    routes: dict[str, Route] = field(default_factory=dict)
    def add(self, key, points, source=None, target=None, parts=(), kind='external'):
        route=Route(key,tuple(points),source,target,tuple(parts),kind)
        _=route.d
        if key in self.routes or any(a==b for a,b in zip(route.points,route.points[1:])):
            raise ValueError('Duplicate route or zero-length segment')
        for ref,endpoint in ((source,route.points[0]),(target,route.points[-1])):
            if ref and self.nodes[ref[0]].port(ref[1]) != endpoint:
                raise ValueError(f'Route {key} does not meet {ref}')
        self.routes[key]=route
        return route
    def record(self, scene):
        scene.numeric.setdefault('diagram_layouts',[]).append({
            'case':self.case,'variant':self.variant,'width':self.width,'height':self.height,
            'nodes':{k:{'box':n.box,'shape':n.shape} for k,n in self.nodes.items()},
            'routes':{k:{'points':r.points,'d':r.d,'source':r.source,'target':r.target,'parts':r.parts,'kind':r.kind} for k,r in self.routes.items()}})


def cascade_layout(narrow=False):
    if not narrow:
        nodes={'lb':Node('lb',40,200,160,108),'db':Node('db',820,200,160,108)}
        nodes.update({f's{i}':Node(f's{i}',390,44+i*156,240,108) for i in range(3)})
        l=Layout('cluster-cascade','wide',1000,514,nodes)
        l.add('arrival',[(4,254),nodes['lb'].port('left')],target=('lb','left'))
        for i in range(3):
            l.add(f'dispatch-{i}',[nodes['lb'].port('right'),nodes[f's{i}'].port('left')],('lb','right'),(f's{i}','left'))
            l.add(f'dependency-{i}',[nodes[f's{i}'].port('right'),nodes['db'].port('left')],(f's{i}','right'),('db','left'))
        l.add('rejected',[nodes['lb'].port('top'),(120,156)],('lb','top'))
    else:
        nodes={'lb':Node('lb',100,44,200,94),'db':Node('db',100,720,200,94)}
        nodes.update({f's{i}':Node(f's{i}',100,220+i*156,200,108) for i in range(3)})
        l=Layout('cluster-cascade','narrow',400,858,nodes)
        l.add('arrival',[(200,6),nodes['lb'].port('top')],target=('lb','top'))
        # Each trunk is a real shared route junction, not three superimposed strokes.
        l.add('dispatch-trunk',[nodes['lb'].port('bottom'),(200,174),(44,174),(44,586)],('lb','bottom'))
        l.add('dependency-trunk',[(356,274),(356,674),(200,674),nodes['db'].port('top')],target=('db','top'))
        for i in range(3):
            n=nodes[f's{i}']; y=n.port('left')[1]
            l.add(f'dispatch-branch-{i}',[(44,y),n.port('left')],target=(f's{i}','left'))
            l.add(f'dependency-branch-{i}',[n.port('right'),(356,y)],(f's{i}','right'))
            l.add(f'dispatch-{i}',[nodes['lb'].port('bottom'),(200,174),(44,174),(44,y),n.port('left')],('lb','bottom'),(f's{i}','left'),['dispatch-trunk',f'dispatch-branch-{i}'])
            l.add(f'dependency-{i}',[n.port('right'),(356,y),(356,674),(200,674),nodes['db'].port('top')],(f's{i}','right'),('db','top'),[f'dependency-branch-{i}','dependency-trunk'])
        l.add('rejected',[nodes['lb'].port('right'),(354,91)],('lb','right'))
    return l


def event_layout(narrow=False):
    if not narrow:
        nodes={'queue':Node('queue',40,170,200,216),'loop':Node('loop',406,184,188,188,'circle'),
               'answer':Node('answer',800,224,160,108),'io':Node('io',362,464,276,110)}
        l=Layout('event-loop','wide',1000,646,nodes)
        l.add('arrival',[(6,278),nodes['queue'].port('left')],target=('queue','left'))
        l.add('dispatch',[nodes['queue'].port('right'),nodes['loop'].port('left')],('queue','right'),('loop','left'))
        l.add('response',[nodes['loop'].port('right'),nodes['answer'].port('left')],('loop','right'),('answer','left'))
        l.add('delegate',[nodes['loop'].port('bottom'),nodes['io'].port('top')],('loop','bottom'),('io','top'))
        l.add('callback',[nodes['io'].port('left'),(140,519),nodes['queue'].port('bottom')],('io','left'),('queue','bottom'))
    else:
        nodes={'queue':Node('queue',134,44,208,188),'loop':Node('loop',146,320,184,184,'circle'),
               'answer':Node('answer',134,598,208,108),'io':Node('io',134,788,208,116)}
        l=Layout('event-loop','narrow',440,990,nodes)
        l.add('arrival',[(238,6),nodes['queue'].port('top')],target=('queue','top'))
        l.add('dispatch',[nodes['queue'].port('bottom'),nodes['loop'].port('top')],('queue','bottom'),('loop','top'))
        l.add('response',[nodes['loop'].port('bottom'),nodes['answer'].port('top')],('loop','bottom'),('answer','top'))
        l.add('delegate',[nodes['loop'].port('right'),(402,412),(402,758),(238,758),nodes['io'].port('top')],('loop','right'),('io','top'))
        l.add('callback',[nodes['io'].port('left'),(44,846),(44,138),nodes['queue'].port('left')],('io','left'),('queue','left'))
    return l


def pipeline_layout(narrow=False):
    if not narrow:
        nodes={k:Node(k,24+256*i,70,176,126) for i,k in enumerate(('gateway','queue','application','database'))}
        l=Layout('pipeline-bottleneck','wide',1000,272,nodes);entry='left';exit='right';origin=(0,133);sink=(1000,133)
    else:
        nodes={k:Node(k,96,42+190*i,208,126) for i,k in enumerate(('gateway','queue','application','database'))}
        l=Layout('pipeline-bottleneck','narrow',400,818,nodes);entry='top';exit='bottom';origin=(200,4);sink=(200,780)
    l.add('arrival',[origin,nodes['gateway'].port(entry)],target=('gateway',entry))
    keys=list(nodes)
    for a,b in zip(keys,keys[1:]):l.add(f'{a}-{b}',[nodes[a].port(exit),nodes[b].port(entry)],(a,exit),(b,entry))
    l.add('exit',[nodes['database'].port(exit),sink],('database',exit))
    return l
