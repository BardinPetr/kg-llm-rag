import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import *
from uuid import uuid4
from copy import copy
import cv2
import networkx as nx
from bidict import bidict
from shapely import LineString, Polygon, Point, STRtree

from utils.gui import to_rgb_or_copy, color_range_01
from utils.utils import imap


def pt_c(x: Point) -> Tuple[int, int]:
    return imap(list(x.coords[0]))


def uid():
    return str(uuid4().hex)


@dataclass
class Segment:
    l: LineString

    @classmethod
    def of_segment(cls, seg):
        return Segment(l=LineString(seg))


class NType(StrEnum):
    UNBOUND = "UB"
    BOUND_START = "BS"
    BOUND_END = "BE"
    BOUND_INT = "BI"
    OBJECT = "OB"
    ARROWHEAD = "AH"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class GNode:
    pt: Point
    box: Optional[Polygon] = None
    typ: NType = NType.UNBOUND
    uid: str = field(default_factory=uid)

    def __str__(self):
        return f"P({self.uid[:3]}){self.typ}{imap(self.pt.coords[0])}"

    def __repr__(self):
        return str(self)


class CType(StrEnum):
    HARD = "H"
    SOFT = "S"
    POSS = "p"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class GEdge:
    typ: CType
    nds: Optional[Tuple[GNode, GNode]] = None

    def __str__(self):
        return f"E/{self.typ}({self.nds})"

    def __repr__(self):
        return str(self)

    @property
    def pts(self) -> Tuple[Point, Point]:
        return self.nds[0].pt, self.nds[1].pt

    @property
    def u_start(self) -> str:
        return self.nds[0].uid

    @property
    def u_end(self) -> str:
        return self.nds[-1].uid

@dataclass
class LineGraph:
    g: nx.Graph
    strt: STRtree
    strt_enc: bidict[str, int]

    def __init__(self):
        self.g = nx.Graph()
        self.strt = STRtree([])
        self.strt_enc = bidict()

    """"""

    def add_segments(self, segments: List[Tuple[Point, Point]]):
        for pt2 in segments:
            uids = []
            for i in pt2:
                t = GNode(pt=i)
                self.add_node(t)
                uids.append(t.uid)
            self.add_edge(*uids, CType.HARD)
        self.recalc()

    """"""

    def add_node(self, t: GNode):
        self.g.add_node(t.uid, x=t)

    def add_edge(self, nid1, nid2, typ):
        self.g.add_edge(nid1, nid2, x=GEdge(typ))

    def get_edge(self, uid1, uid2) -> Optional[GEdge]:
        return self.g.get_edge_data(uid1, uid2, {"x": None})["x"]

    def connect(self, nid1, nid2, e_con_type: CType, n_type: NType):
        self.mark_node(nid1, n_type)
        self.mark_node(nid2, n_type)
        self.add_edge(nid1, nid2, e_con_type)

    """"""

    def node(self, uid: str) -> GNode:
        return self.g.nodes[uid]['x']

    def nodes(self, uids: List[str] = None) -> List[GNode]:
        all_n: Dict[str, GNode] = dict(self.g.nodes(data='x'))
        if uids is None: return list(all_n.values())
        return [i
                for uid in uids
                if (i := all_n.get(uid, None)) is not None]

    def fnodes(self, flt: Callable[[GNode], bool]) -> List[GNode]:
        return list(filter(flt, self.nodes()))

    def neighbors(self, uid, edge_typ=None) -> List[GEdge]:
        nb_con = self.g.edges(uid, data="x")
        out = []
        for *uids, x_link in nb_con:
            assert uids[0] == uid
            link = copy(x_link)
            link.nds = self.nodes(uids)
            if edge_typ is None or link.typ == edge_typ:
                out.append(link)
        return out

    def unbound_nodes(self) -> List[GNode]:
        return [i for i in self.nodes() if i.typ == NType.UNBOUND]

    def networks(self, edge_types=None) -> List[nx.Graph]:
        edge_types = edge_types or {CType.HARD, CType.SOFT}

        def edge_filter(n1, n2):
            return self.g[n1][n2]['x'].typ in edge_types

        filtered_graph = nx.subgraph_view(self.g, filter_edge=edge_filter)
        components = nx.connected_components(filtered_graph)
        return [filtered_graph.subgraph(i).copy() for i in components]

    """"""

    def propose_link(self, nid1, nid2) -> GEdge:
        nds = self.nodes([nid1, nid2])
        return GEdge(CType.POSS, nds)

    def propose_for_node(self, nid1):
        node = self.node(nid1)
        if node.typ != NType.UNBOUND: return None
        all_our_ids = [i.nds[1].uid for i in self.neighbors(nid1)] + [nid1]

        our_edge_ends = self.neighbors(nid1, edge_typ=CType.HARD)
        if len(our_edge_ends) > 1: return None
        our_edge = our_edge_ends[0]  # from "node" to other

        # print(f"@@@@@ for {node}")
        possible_starts = self.nearby_nodes(nid1, 20)
        possible_next_edges: List[GEdge] = []
        for ps_start in possible_starts:
            if ps_start.typ != NType.UNBOUND: continue
            if ps_start.uid in all_our_ids: continue
            # print(ps_start)
            ps_edges = self.neighbors(ps_start.uid, edge_typ=CType.HARD)
            ps_edges = [i for i in ps_edges if i.nds[0].typ == NType.UNBOUND and i.nds[1].typ == NType.UNBOUND]
            if len(ps_edges) != 1: continue
            possible_next_edges.append(ps_edges[0])

        if not possible_next_edges: return None
        return our_edge, possible_next_edges

    def mark_node(self, nid, typ):
        self.node(nid).typ = typ

    """"""

    def nearby_nodes(self, uid: str, distance: float) -> List[GNode]:
        n_ids = self.strt.query(self.node(uid).pt, predicate="dwithin", distance=distance)
        nodes = [self.node(self.strt_enc.inverse[i]) for i in n_ids]
        return nodes

    def recalc(self):
        n_list = self.nodes()
        n_list.sort(key=lambda i: i.uid)
        self.strt_enc = bidict({n.uid: idx for idx, n in enumerate(n_list)})
        self.strt = STRtree([i.pt for i in n_list])

    """"""

    def vis(self, base_img):
        nclr = {
            # NType.UNBOUND: None,
            NType.UNBOUND: (255, 0, 0),
            NType.BOUND_INT: (0, 255, 0),
            NType.BOUND_START: (0, 255, 255)
        }

        im = to_rgb_or_copy(base_img)

        for i in self.nodes():
            if c := nclr[i.typ]:
                cv2.circle(im, pt_c(i.pt), 5, c, 1)

        comps = self.networks()
        for comp in comps:
            col = color_range_01(random.random())
            for *nds, data in comp.edges(data='x'):
                pa, pb = [pt_c(i.pt) for i in self.nodes(nds)]
                cv2.line(im, pa, pb, col, 1)

        return im
