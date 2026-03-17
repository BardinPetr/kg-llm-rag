import random
from copy import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import *
from uuid import uuid4

import cv2
import networkx as nx
import numpy as np
from bidict import bidict
from shapely import LineString, Polygon
from shapely import Point, STRtree

from utils.gui import to_rgb_or_copy, color_range_01, pt_c
from utils.utils import imap
from visual.analyze.ocr.model import OCRText
from visual.analyze.structure.node import ImageGraphNode


def uid():
    return str(uuid4().hex)


class BaseObj(Protocol):
    uid: str


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
    TEXTBOX = "TE"
    ARROWHEAD = "AH"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class GNode:
    pt: Point | Polygon
    data: Any = None
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


def score_partial(val, v_min, v_max):
    scaled = (val - v_min) / (v_max - v_min)
    return scaled if v_min <= val <= v_max else np.inf


def rank_pairs(ranker, own_seg: GEdge, others: List[GEdge], max_score=1) -> List[Tuple[float, GEdge]]:
    variants = [(score, i)
                for i in others
                if (score := ranker(own_seg, i)) < max_score]
    variants.sort(key=lambda i: i[0])
    return variants


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

    def add_objects(self, objects: List[ImageGraphNode]):
        for i in objects:
            t = GNode(pt=i.box.centroid, data=i, typ=NType.OBJECT, uid=i.id)
            self.add_node(t)

    def add_texts(self, objects: List[OCRText]):
        for i in objects:
            t = GNode(pt=i.bbox.polygon().centroid, data=i, typ=NType.TEXTBOX)
            self.add_node(t)

    def add_arrowheads(self, objects: List[Point]):
        for i in objects:
            self.add_node(GNode(pt=i, typ=NType.ARROWHEAD))

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

    def mark_node(self, nid, typ):
        self.node(nid).typ = typ

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

    def propose_for_node(self, nid1, search_radius=20):
        node = self.node(nid1)
        if node.typ != NType.UNBOUND: return None
        all_our_ids = [i.nds[1].uid for i in self.neighbors(nid1)] + [nid1]

        our_edge_ends = self.neighbors(nid1, edge_typ=CType.HARD)
        if len(our_edge_ends) > 1: return None
        our_edge = our_edge_ends[0]  # from "node" to other

        possible_starts = self.nearby_nodes(nid1, search_radius)
        possible_next_edges: List[GEdge] = []
        for ps_start in possible_starts:
            if ps_start.typ != NType.UNBOUND: continue
            if ps_start.uid in all_our_ids: continue
            ps_edges = self.neighbors(ps_start.uid, edge_typ=CType.HARD)
            ps_edges = [i for i in ps_edges if i.nds[0].typ == NType.UNBOUND]
            if len(ps_edges) != 1: continue
            possible_next_edges.append(ps_edges[0])

        if not possible_next_edges: return None
        return our_edge, possible_next_edges

    def connect_softly(self, scorer: Callable[[GEdge, GEdge], float], max_score=1, search_radius=20):
        for node in self.unbound_nodes():
            if node.typ != NType.UNBOUND: continue
            if (proposal := self.propose_for_node(node.uid, search_radius)) is None: continue
            cur_edge, proposed_edges = proposal

            variants = rank_pairs(scorer, cur_edge, proposed_edges, max_score)
            if len(variants) == 0: continue

            score, other_edge = variants[0]
            self.connect(cur_edge.u_start, other_edge.u_start, CType.SOFT, NType.BOUND_INT)

    def connect_terminals(self, scorer: Callable[[GEdge, GEdge], float], max_dist):
        for node in self.unbound_nodes():
            pass

    """"""

    def nearby_nodes(self, uid: str, distance: float) -> List[GNode]:
        n_ids = self.strt.query(self.node(uid).pt, predicate="dwithin", distance=distance)
        nodes = [self.node(self.strt_enc.inverse[i]) for i in n_ids]
        return nodes

    def recalc(self):
        n_list = [i for i in self.nodes() if i.typ in {
            NType.UNBOUND,
            NType.BOUND_INT,
            NType.BOUND_START,
            NType.BOUND_END,
            NType.ARROWHEAD,
            NType.TEXTBOX
        }]
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
                cv2.line(im, pa, pb, col, 2)

        return im
