import re

import cv2
import networkx as nx
from matplotlib import pyplot as plt
from rdp import rdp

from src.utils.prob import choose
from src.visual.models.diagram import *

DPI = 70

pt2in = lambda x: x / 72
in2pt = lambda x: x * 72
pt2px = lambda x: pt2in(x) * DPI
px2pt = lambda x: in2pt(x / DPI)
in2px = lambda x: pt2px(in2pt(x))

PAD_IN = 0.2
PAD_PX = in2px(PAD_IN)


def render_graph(g: nx.DiGraph, out_file):
    G = nx.nx_agraph.to_agraph(g)
    G.graph_attr['dpi'] = DPI
    G.graph_attr['pad'] = PAD_IN
    G.graph_attr['margin'] = 0
    # G.graph_attr['layout'] = "neato"
    # G.graph_attr['overlap'] = "false"
    # G.graph_attr['nodesep'] = 0.2
    # G.graph_attr['ranksep'] = 0.2
    G.graph_attr['splines'] = choose(
        3, "curved",
        # 2, "ortho",
        # 2, "true",
        1, "polyline",
        # 1, "line"
    )
    G.layout(prog='dot')
    G.draw(out_file)

    img = cv2.imread(out_file)
    res = DiagramDescription(shape = img.shape[1::-1])

    *_, g_width, g_height = [pt2px(float(i)) for i in G.graph_attr['bb'].split(',')]
    eps = 0.01 * max(g_width, g_height)

    for edge_ids in G.edges():
        e = G.get_edge(*edge_ids)
        if 'pos' in e.attr:
            end_typ, *line = re.split(r"[,\s]", e.attr['pos'])
            line = fmap(line)
            line = [imap((pt2px(i) + PAD_PX, g_height - pt2px(j) + PAD_PX))
                    for i, j in zip(line[::2], line[1::2])]
            if end_typ == 'e': line.append(line.pop(0))
            line = rdp(line, epsilon=eps)
            line = imapn(line)
            data = g.edges[edge_ids]
            res.edges.append(DiagramEdge(
                src_id=edge_ids[0],
                dst_id=edge_ids[1],
                points=line,
                label=data.get('label', ""),
                type=data.get('type', None),
                props=dict_drop_key(data, {'label'})
            ))
            for i, j in zip(line[:-1], line[1:]):
                cv2.line(img, i, j, (0, 255, 0), 2)
                cv2.circle(img, i, 2, (0, 100, 0), -1)
                cv2.circle(img, line[0], 3, (0, 0, 255), -1)
                cv2.circle(img, line[-1], 3, (255, 0, 0), -1)

    for node_id in G.nodes():
        n = G.get_node(node_id)
        if 'pos' in n.attr:
            pos = [pt2px(float(i)) for i in n.attr['pos'].split(',')]
            pos = (pos[0] + PAD_PX, g_height - pos[1] + PAD_PX)
            dim = [int(in2px(float(i))) for i in [n.attr.get('width', 0), n.attr.get('height', 0)]]
            bbox = BBox.of_cxcywh(*pos, *dim)
            data = g.nodes[node_id]
            res.nodes[node_id] = DiagramNode(
                id=node_id,
                bbox=bbox,
                label=data.get('label', ""),
                type=data.get('type', None),
                props=dict_drop_key(data, {'label', 'type', 'id'})
            )
            # cv2.rectangle(img, bbox.p1, bbox.p2, (255, 0, 255), 5)

    # cv2.imwrite(out_file, img)
    # plt.imshow(img)
    return res, img
