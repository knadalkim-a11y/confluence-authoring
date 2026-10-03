"""Geometry invariants, not a claim of original-site visual equivalence."""
import json,math,re,sys,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from diagram_layout import cascade_layout,event_layout,pipeline_layout,Node,Layout
from monitoring_cases import build_case
from validate_html_macro import validate

LAYOUTS=[f(n) for f in (cascade_layout,event_layout,pipeline_layout) for n in (False,True)]

def on_segment(p,a,b,tol=1e-6):
    return abs(math.dist(a,p)+math.dist(p,b)-math.dist(a,b))<tol

def inside_rect_segment(a,b,n):
    # Open interior, excludes legal boundary ports. Slab intersection.
    low=0.;high=1.;pad=.001
    for v,d,mn,mx in ((a[0],b[0]-a[0],n.x+pad,n.x+n.w-pad),(a[1],b[1]-a[1],n.y+pad,n.y+n.h-pad)):
        if abs(d)<1e-9:
            if not mn<v<mx:return False
        else:
            t,u=sorted(((mn-v)/d,(mx-v)/d));low=max(low,t);high=min(high,u)
    return low<high and high>0 and low<1

class Collector(HTMLParser):
    def __init__(self):super().__init__();self.paths=[];self.particles=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='path' and 'data-edge-id' in a:self.paths.append(a)
        if tag=='circle' and 'data-motion-edge' in a:self.particles.append(a)

class LayoutTests(unittest.TestCase):
    def test_rectangles_do_not_overlap(self):
        for l in LAYOUTS:
            ns=list(l.nodes.values())
            for i,a in enumerate(ns):
                for b in ns[i+1:]:
                    self.assertFalse(max(a.x,b.x)<min(a.x+a.w,b.x+b.w) and max(a.y,b.y)<min(a.y+a.h,b.y+b.h),(l.case,l.variant,a,b))
    def test_all_nodes_inside_canvas(self):
        for l in LAYOUTS:
            for n in l.nodes.values():self.assertTrue(0<=n.x<n.x+n.w<=l.width and 0<=n.y<n.y+n.h<=l.height)
    def test_same_role_servers_align_size_and_gap(self):
        for l in (cascade_layout(),cascade_layout(True)):
            a,b,c=[l.nodes[f's{i}'] for i in range(3)]
            self.assertEqual((a.x,a.w,a.h),(b.x,b.w,b.h));self.assertEqual((b.x,b.w,b.h),(c.x,c.w,c.h));self.assertEqual(b.y-a.y,c.y-b.y)
    def test_wide_cascade_centres_and_horizontal_spacing(self):
        l=cascade_layout();a,b,c=[l.nodes[x] for x in ('lb','s1','db')]
        self.assertEqual(a.port('right')[1],b.port('left')[1]);self.assertEqual(b.port('right')[1],c.port('left')[1]);self.assertEqual(b.x-a.x-a.w,c.x-b.x-b.w)
    def test_pipeline_equal_spacing(self):
        for narrow in (False,True):
            ns=list(pipeline_layout(narrow).nodes.values());gaps=[b.y-a.y-a.h if narrow else b.x-a.x-a.w for a,b in zip(ns,ns[1:])];self.assertEqual(len(set(gaps)),1)
    def test_cardinal_ports_at_actual_boundary(self):
        for l in LAYOUTS:
            for r in l.routes.values():
                for ref,p in ((r.source,r.points[0]),(r.target,r.points[-1])):
                    if ref:self.assertEqual(p,l.nodes[ref[0]].port(ref[1]))
    def test_straight_or_orthogonal_no_bezier(self):
        for l in LAYOUTS:
            for r in l.routes.values():
                self.assertFalse(re.search('[QCAqca]',r.d))
                if len(r.points)>2:
                    for a,b in zip(r.points,r.points[1:]):self.assertTrue(a[0]==b[0] or a[1]==b[1],(l.case,r.key,a,b))
    def test_rails_do_not_pass_through_nodes(self):
        for l in LAYOUTS:
            for r in l.routes.values():
                for a,b in zip(r.points,r.points[1:]):
                    for n in l.nodes.values():self.assertFalse(inside_rect_segment(a,b,n),(l.case,l.variant,r.key,n.key,a,b))
    def test_no_unintended_proper_edge_crossings(self):
        def cross(a,b,c,d):
            orient=lambda p,q,r:(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
            return orient(a,b,c)*orient(a,b,d)<-1e-6 and orient(c,d,a)*orient(c,d,b)<-1e-6
        for l in LAYOUTS:
            seg=[(k,a,b) for k,r in l.routes.items() if not r.parts for a,b in zip(r.points,r.points[1:])]
            for i,(k,a,b) in enumerate(seg):
                for key,c,d in seg[i+1:]:self.assertFalse(cross(a,b,c,d),(l.case,l.variant,k,key))
    def test_shared_path_is_covered_by_visible_trunks(self):
        for l in LAYOUTS:
            for r in l.routes.values():
                if not r.parts:continue
                segments=[(a,b) for key in r.parts for a,b in zip(l.routes[key].points,l.routes[key].points[1:])]
                for j in range(201):self.assertTrue(any(on_segment(r.at(j/200),a,b) for a,b in segments),(l.variant,r.key,j))
    def test_particle_geometry_and_rail_use_same_serialization(self):
        cases=json.loads((ROOT/'examples/monitoring-cases.json').read_text())['cases']
        for c in cases:
            if c['id'] not in ('cluster-cascade','event-loop','pipeline-bottleneck'):continue
            frag,m=build_case(c,'ca-layout-unit');parser=Collector();parser.feed(frag)
            expected={(r['d'],k) for layout in m['diagram_layouts'] for k,r in layout['routes'].items()}
            self.assertTrue(parser.paths);self.assertTrue(parser.particles);self.assertFalse(validate(frag))
            for token in parser.particles:self.assertIn((token['data-motion-path'],token['data-motion-edge']),expected)
            for rail in parser.paths:self.assertIn((rail['d'],rail['data-edge-id']),expected)
    def test_invalid_port_or_route_rejected(self):
        n=Node('a',0,0,10,10);l=Layout('x','wide',100,100,{'a':n})
        with self.assertRaises(ValueError):n.port('diagonal')
        with self.assertRaises(ValueError):l.add('bad',[(9,5),(20,5)],('a','right'))
        with self.assertRaises(ValueError):l.add('nan',[(0,0),(float('nan'),5)])

if __name__=='__main__':unittest.main()
