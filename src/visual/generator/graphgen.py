import random
from uuid import uuid4

import networkx as nx
from faker import Faker

from src.utils.prob import choose

fake = Faker('ru-RU')


def gg_id():
    return str(uuid4().hex)


def gg_action(g: nx.DiGraph, current_node):
    graph_sz = len(g.nodes)
    comp_sz = len(nx.node_connected_component(g.to_undirected(), current_node)) if current_node else 0
    # spread = 10 / max(10, graph_sz)
    spread = 1 if 0 < comp_sz < 10 else 0.3
    if not comp_sz: spread = 0
    split = 1 if comp_sz == 0 else 0
    # split = 1 if comp_sz == 0 or graph_sz < 5 else 0
    return choose(
        spread * 2, dict(action='node', direction='out'),
        spread * 1, dict(action='node', direction='in'),
        2 if len(g.nodes) > 5 else 0, dict(action='stop'),
        split * 0.5, dict(action='head'),
    )


def gg_top():
    uid = gg_id()
    return uid, dict(id=uid, type='company', label=fake.company())


def gg_node(g: nx.DiGraph, cur_id, direction):
    current = g.nodes[cur_id]
    can_be_company = int(direction == 'out' or direction == 'in' and current['type'] == 'company')
    can_be_person = int(direction == 'in' and current['type'] == 'company')
    if not any([can_be_company, can_be_person]): return None
    typ = choose(
        1 * can_be_company, 'company',
        1 * can_be_person, 'person'
    )
    shape = choose(
        5, "box",
        3, "ellipse",
        3, "parallelogram",
        3, "diamond",
        # 1, "plaintext"
    )

    label = fake.name() if typ == 'person' else fake.company()
    new_id = gg_id()

    node_data = dict(
        type=typ,
        label=label,
        id=new_id,
        shape=shape
    )
    edge_data = dict(xlabel=f"{random.random() * 100:.1f}%")
    new_edge = [cur_id, new_id][::(-1 if direction == 'in' else 1)]
    return new_id, node_data, new_edge, edge_data


def graphgen(g: nx.DiGraph, current_node_id=None):
    while True:
        match gg_action(g, current_node_id):
            case {"action": "node", "direction": link_dir}:
                x = gg_node(g, current_node_id, link_dir)
                if not x: continue
                new_id, node_data, new_edge, edge_data = x
                g.add_node(new_id, **node_data)
                g.add_edge(*new_edge, **edge_data)
                graphgen(g, new_id)
            case {"action": "head"}:
                top_id, top = gg_top()
                g.add_node(top_id, **top)
                current_node_id = top_id
            case {"action": "stop"}:
                break
            case _:
                continue

# ds_clear()
# for _ in range(10):
#     ds_one(0)
