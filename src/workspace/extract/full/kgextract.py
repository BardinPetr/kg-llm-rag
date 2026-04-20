from dataclasses import dataclass
from typing import *

import networkx as nx
from langchain_core.messages import SystemMessage, HumanMessage

from utils.func import disk_cache
from utils.prompt import sprompt, uprompt

SEP = ":::"


@dataclass
class EntityKG:
    uid: str
    type: str
    name: str
    ref_pos: int


@dataclass
class FactKG:
    uid: str
    type: str
    value: Optional[str]
    ref_pos: int


from fuzzysearch import find_near_matches


# todo: instruct llm to use only sequential strings as references
@disk_cache("ccache")
def _load_ref(ordoc, s_exc):
    s_exc = s_exc.lower()
    ref_pos = ordoc.find(s_exc)
    if ref_pos < 0 and (l_matches := find_near_matches(s_exc, ordoc, max_l_dist=5)):
        return l_matches[0].start
    return ref_pos


def _load_entity(ordoc, row):
    if row.count(SEP) != 4: return None
    _, eid, etyp, enam, eref = row.split(SEP)
    return EntityKG(uid=eid, type=etyp, name=enam, ref_pos=_load_ref(ordoc, eref))


def _load_fact(ordoc, row):
    if row.count(SEP) != 3: return None
    fid, ftyp, fval, fref = row.split(SEP)
    if fid == "EDGE": return None
    return FactKG(uid=fid, type=ftyp, value=fval if fval != "REL" else None, ref_pos=_load_ref(ordoc, fref))


def _load_edge(row):
    if row.count(SEP) != 3: return None
    fid, e_typ, e_from, e_to = row.split(SEP)
    if fid != "EDGE": return None
    return e_from, e_to, dict(data=e_typ)


def _load_facts(ordoc, txt, kgg):
    facts = []
    fact_edges = []
    for i in txt.strip().split("\n"):
        if e := _load_edge(i):
            fact_edges.append(e)
        elif e := _load_fact(ordoc, i):
            facts.append(e)
            kgg.add_node(e.uid, data=e)
    kgg.add_edges_from(fact_edges)
    return facts, fact_edges


def _load_entities(ordoc, txt, kgg):
    res = []
    for i in txt.strip().split("\n"):
        if e := _load_entity(ordoc, i):
            kgg.add_node(e.uid, data=e)
            res.append(e)
    return res


def llm_text_dec(x):
    b = bytes(x.content, 'utf-8').decode('unicode_escape')
    try:
        b = b.encode('latin1').decode('utf-8')
    except:
        pass
    return b


def doc_extract_kg(llm, doc_txt) -> nx.DiGraph:
    print("extracting entities")
    kg_e_msgs = [
        SystemMessage(sprompt("kge", "entity")),
        HumanMessage(uprompt("kge", "entity", document=doc_txt, existing_classes=[]))
    ]
    kg_e_res = llm.invoke(kg_e_msgs)
    kg_e_res_txt = llm_text_dec(kg_e_res)

    print("extracting relation facts")
    kg_fr_msgs = [
        SystemMessage(sprompt("kge", "relfact")),
        HumanMessage(uprompt("kge", "relfact", document=doc_txt, existing_fact_classes=[], entities=kg_e_res_txt))
    ]
    kg_fr_res = llm.invoke(kg_fr_msgs)
    kg_fr_res_txt = llm_text_dec(kg_fr_res)

    print("extracting value facts")
    kg_fv_msgs = [
        SystemMessage(sprompt("kge", "relval")),
        HumanMessage(uprompt("kge", "relval", document=doc_txt, existing_fact_classes=[], entities=kg_e_res_txt,
                             relation_facts=kg_fr_res_txt))
    ]
    kg_fv_res = llm.invoke(kg_fv_msgs)
    kg_fv_res_txt = llm_text_dec(kg_fv_res)

    print("done extracting")

    doc_kg = nx.DiGraph()

    entities = _load_entities(doc_txt, kg_e_res_txt, doc_kg)
    ec = set([i.type for i in entities])
    print(f"Loaded entity classes: {ec}")
    print(f"Loaded {len(entities)} entities")

    r_facts, r_fact_edges = _load_facts(doc_txt, kg_fr_res_txt, doc_kg)
    ec = set([i.type for i in r_facts])
    print(f"Loaded r-fact classes: {ec}")
    print(f"Loaded {len(r_facts)} r-facts and {len(r_fact_edges)} edges")

    v_facts, v_fact_edges = _load_facts(doc_txt, kg_fv_res_txt, doc_kg)
    ec = set([i.type for i in v_facts])
    print(f"Loaded v-fact classes: {ec}")
    print(f"Loaded {len(v_facts)} v-facts and {len(v_fact_edges)} edges")

    return doc_kg


def gvis(g):
    from pyvis.network import Network
    nt = Network('100%', '100%')
    nt.from_nx(g)
    nt.show('nx.html', notebook=False)
