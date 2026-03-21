import random
from copy import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import *
from uuid import uuid4

import cv2
import networkx as nx
from bidict import bidict
from shapely import LineString, Polygon
from shapely import Point, STRtree

from src.utils.gui import to_rgb_or_copy, color_range_01, pt_c
from src.utils.utils import imap
from src.visual.analyze.ocr.model import OCRText
from src.visual.analyze.structure.node import ImageGraphNode


def uid():
    return str(uuid4().hex)


import numpy as np
from shapely.geometry.base import BaseGeometry
from typing import List, Tuple


def find_mutual_nearest_pairs(
        objects_a: List[BaseGeometry],
        objects_b: List[BaseGeometry],
        max_distance: float
) -> np.ndarray:
    if len(objects_a) == 0 or len(objects_b) == 0:
        return np.array([]).reshape(0, 2).astype(int)

    n_a = len(objects_a)
    n_b = len(objects_b)
    distance_matrix = np.zeros((n_a, n_b))
    for i, obj_a in enumerate(objects_a):
        for j, obj_b in enumerate(objects_b):
            distance_matrix[i, j] = obj_a.distance(obj_b)

    nearest_b_for_a = np.argmin(distance_matrix, axis=1)
    nearest_a_for_b = np.argmin(distance_matrix, axis=0)
    pairs = []
    used_a = set()
    used_b = set()
    for i in range(n_a):
        if i in used_a: continue
        j = nearest_b_for_a[i]
        if j in used_b: continue
        if nearest_a_for_b[j] == i:
            dist = distance_matrix[i, j]
            if dist <= max_distance:
                pairs.append([i, j])
                used_a.add(i)
                used_b.add(j)
    return np.array(pairs, dtype=int).reshape(-1, 2)


def extend_segment_beyond(point_a: Point, point_b: Point, extension_length: float) -> Tuple[Point, Point]:
    ax, ay = point_a.x, point_a.y
    bx, by = point_b.x, point_b.y
    dx = bx - ax
    dy = by - ay
    distance_ab = np.sqrt(dx ** 2 + dy ** 2)
    if distance_ab == 0:
        raise ValueError("Points A and B must be different (not coincident)")
    unit_dx = dx / distance_ab
    unit_dy = dy / distance_ab
    extended_x = bx + extension_length * unit_dx
    extended_y = by + extension_length * unit_dy
    return Point(ax, ay), Point(extended_x, extended_y)


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
    BOUND_INT = "BI"
    OBJECT = "OB"
    TEXTBOX = "TE"
    ARROWHEAD = "AH"
    SOFT_DELETE = "--"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class GNode:
    pt: Point | Polygon
    bound: bool = False
    data: Any = None
    typ: NType = NType.UNBOUND
    uid: str = field(default_factory=uid)

    def __str__(self):
        return f"P({self.uid[:3]}){self.typ}{imap(self.pt.coords[0]) if isinstance(self.pt, Point) else "P"}"

    def __repr__(self):
        return str(self)


class CType(StrEnum):
    HARD = "H"
    SOFT = "S"
    TERM = "T"
    POSS = "p"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class GEdge:
    typ: CType
    nds: Optional[Tuple[GNode, GNode]] = None
    data: List[Any] = field(default_factory=list)

    def __str__(self):
        return f"E/{self.typ}({self.nds})"

    def __repr__(self):
        return str(self)

    @property
    def pts(self) -> Tuple[Point, Point]:
        return self.nds[0].pt, self.nds[1].pt

    @property
    def pt(self):
        return LineString(self.pts)

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


def rank_pairs_list(ranker, a_seg: List[GEdge], b_seg: List[GEdge], max_score=1) -> List[Tuple[float, GEdge, GEdge]]:
    variants = [(score, a, b)
                for a, b in zip(a_seg, b_seg)
                if (score := ranker(a, b)) < max_score]
    variants.sort(key=lambda i: i[0])
    return variants


class GeomTree:
    def __init__(self, objects):
        self._data = objects.copy()
        self.strt = STRtree([i.pt for i in self._data])

    def nearby(self, geo: BaseGeometry, distance: float, predicate="dwithin") -> List[Any]:
        n_ids = self.strt.query(geo, predicate=predicate, distance=distance)
        data = [self._data[i] for i in n_ids]
        return sorted(data, key=lambda i: geo.distance(i.pt))

    def nearest(self, geo: BaseGeometry, max_distance: float, predicate="dwithin") -> Any:
        res = self.nearby(geo, max_distance, predicate)
        return res[0] if len(res) else None


@dataclass
class LineGraph:
    g: nx.Graph
    strt: STRtree
    strt_enc: bidict[str, int]

    def __init__(self):
        self.g = nx.Graph()
        self.strt = STRtree([])
        self.strt_enc = bidict()
        self.obj_tree: GeomTree = None

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
        box_nodes = []
        for i in objects:
            self.add_node(GNode(pt=i.box.centroid, data=i, typ=NType.OBJECT, uid=i.uid))
            box_nodes.append(GNode(pt=i.box, typ=NType.OBJECT, uid=i.uid))
        self.obj_tree = GeomTree(box_nodes)

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

    def snodes(self, typ: NType = None, bound: bool = None) -> List[GNode]:
        return self.fnodes(lambda x: (typ is None or x.typ == typ) and (bound is None or x.bound == bound))

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

    def find_own_edge(self, from_point_uid) -> Optional[GEdge]:
        our_edge_ends = self.neighbors(from_point_uid, edge_typ=CType.HARD)
        if len(our_edge_ends) > 1: return None
        return our_edge_ends[0]

    def propose_for_node(self, nid1, search_radius=20):
        node = self.node(nid1)
        if node.typ != NType.UNBOUND: return None
        all_our_ids = [i.nds[1].uid for i in self.neighbors(nid1)] + [nid1]
        our_edge = self.find_own_edge(nid1)  # from "node" to other

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
            node = self.node(node.uid)
            if node.typ != NType.UNBOUND: continue
            if (proposal := self.propose_for_node(node.uid, search_radius)) is None: continue
            cur_edge, proposed_edges = proposal

            variants = rank_pairs(scorer, cur_edge, proposed_edges, max_score)
            if len(variants) == 0: continue

            score, other_edge = variants[0]
            self.connect(cur_edge.u_start, other_edge.u_start, CType.SOFT, NType.BOUND_INT)

    def connect_arrowheads(self, search_radius):
        for ah in self.snodes(typ=NType.ARROWHEAD, bound=False):
            self.node(ah.uid).typ = NType.SOFT_DELETE
        for ah in self.snodes(typ=NType.ARROWHEAD):
            if nearest_obj := self.obj_tree.nearest(ah.pt, search_radius):
                self.node(ah.uid).bound = True
                self.add_edge(ah.uid, nearest_obj.uid, CType.SOFT)
            else:
                self.node(ah.uid).typ = NType.SOFT_DELETE

    def connect_terminals_ah(self, scorer: Callable[[GEdge, GEdge], float], search_radius):
        for node in self.unbound_nodes():
            node = self.node(node.uid)
            if node.typ != NType.UNBOUND: continue
            our_edge = self.find_own_edge(node.uid)
            if our_edge is None: continue

            possible_terms = [i
                              for i in self.nearby_nodes(node.uid, search_radius)
                              if i.typ == NType.ARROWHEAD and not i.bound]
            possible_term_segs = [GEdge(CType.POSS, nds=(node, i)) for i in possible_terms]
            variants = rank_pairs(scorer, our_edge, possible_term_segs, 1)
            if len(variants) == 0: continue

            score, other_edge = variants[0]
            _, term_node = other_edge.nds

            self.mark_node(node.uid, NType.BOUND_START)
            self.node(term_node.uid).bound = True
            self.add_edge(node.uid, term_node.uid, CType.TERM)

    def connect_terminals(self, search_radius):
        for node in self.unbound_nodes():
            node = self.node(node.uid)
            if node.typ != NType.UNBOUND: continue
            our_edge = self.find_own_edge(node.uid)
            if our_edge is None: continue
            edge_pts = [i.pt for i in our_edge.nds[::-1]]
            extended = extend_segment_beyond(*edge_pts, search_radius)
            els = LineString(extended)
            if intersected_obj := self.obj_tree.nearest(els, search_radius, predicate="intersects"):
                self.mark_node(node.uid, NType.BOUND_START)
                self.add_edge(node.uid, intersected_obj.uid, CType.TERM)

    """"""

    def connect_texts_boxes(self):
        for obj in self.snodes(typ=NType.OBJECT):
            node = self.node(obj.uid)
            box = node.data.box

            texts = self.nearby_nodes(box, distance=0, predicate="covers")
            texts = [i for i in texts if i.typ == NType.TEXTBOX and not i.bound]
            texts_to_join = []
            for i in texts:
                t_node = self.node(i.uid)
                t_node.bound = True
                texts_to_join.append((i.data.bbox.polygon(), i.data.text))
            # TODO
            text = texts_to_join
            node.data.text = text

    def connect_texts_lines(self, search_radius):
        lines = []
        for u1, u2, e in self.g.edges(data='x'):
            if e.typ != CType.HARD: continue
            nds = [self.node(j) for j in [u1, u2]]
            lines.append(GEdge(CType.POSS, nds))

        line_tree = GeomTree(lines)
        for text_n in self.snodes(typ=NType.TEXTBOX, bound=False):
            text_n = self.node(text_n.uid)

            if near := line_tree.nearest(text_n.pt,search_radius):
                text_n.bound = True
                e_idx = near.nds[0].uid, near.nds[1].uid
                self.g.edges[e_idx]['x'].data.append(text_n.data)

    """"""

    def nearby_nodes(self, uid_or_geo: str, distance: float, predicate="dwithin") -> List[GNode]:
        geo = self.node(uid_or_geo).pt if isinstance(uid_or_geo, str) else uid_or_geo
        n_ids = self.strt.query(geo, predicate=predicate, distance=distance)
        nodes = [self.node(self.strt_enc.inverse[i]) for i in n_ids]
        return nodes

    def recalc(self):
        n_list = [i for i in self.nodes() if i.typ in {
            NType.UNBOUND,
            NType.BOUND_INT,
            NType.BOUND_START,
            NType.ARROWHEAD,
            NType.TEXTBOX
        }]
        n_list.sort(key=lambda i: i.uid)
        self.strt_enc = bidict({n.uid: idx for idx, n in enumerate(n_list)})
        self.strt = STRtree([i.pt for i in n_list])

    """"""

    def vis(self, base_img):
        nclr = {
            NType.UNBOUND: (255, 0, 0),
            # NType.BOUND_INT: (0, 255, 0),
            # NType.BOUND_START: (0, 255, 255),
            # NType.ARROWHEAD: (255, 255, 0),
            NType.OBJECT: (255, 0, 255),
            # NType.TEXTBOX: (255, 60, 0),
            NType.SOFT_DELETE: None,
        }

        im = to_rgb_or_copy(base_img)

        for i in self.nodes():
            if c := nclr.get(i.typ, None):
                cv2.circle(im, imap(pt_c(i.pt)), 5, c, -1)

        comps = self.networks()
        for comp in comps:
            col = color_range_01(random.random())
            for *nds, data in comp.edges(data='x'):
                pa, pb = [pt_c(i.pt) for i in self.nodes(nds)]
                cv2.line(im, pa, pb, col, 2)

        return im
