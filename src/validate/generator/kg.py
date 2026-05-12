import re
import time
from typing import *

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from utils.aimodel import load_llm_lc
from utils.json_polyfill import install_json
from utils.prompt import sprompt
from db.store.cacheservice import cache_iput, cache_iget

install_json()

llm = load_llm_lc("gemini3pro")


class KGGenEntity(BaseModel):
    uid: str
    type: str
    canonical_name: str


class KGGenFact(BaseModel):
    uid: str
    type: str
    subject_uid: str


class KGGenRelFact(KGGenFact):
    object_uid: str


class KGGenValFact(KGGenFact):
    object_literal: str


class KGGen(BaseModel):
    domain_overview: str
    entities: Dict[str, KGGenEntity]
    values: Dict[str, KGGenValFact]
    relations: Dict[str, KGGenRelFact]


import networkx as nx


def kggen_out_parse(text: str) -> KGGen:
    overview = None
    entities: Dict[str, KGGenEntity] = {}
    values: Dict[str, KGGenValFact] = {}
    relations: Dict[str, KGGenRelFact] = {}

    text = re.sub(r'<thinking>.*</thinking>', '', text, flags=re.DOTALL)
    for line in text.splitlines():
        if not (line := line.strip()): continue
        if ":::" not in line and not overview:
            overview = line
            continue

        parts = [p.strip() for p in line.strip().split(":::")]
        uid = parts[0]
        try:
            if uid.startswith('E') and len(parts) == 3:
                entities[uid] = KGGenEntity(uid=uid, type=parts[1], canonical_name=parts[2])
            elif uid.startswith('R') and len(parts) == 4:
                relations[uid] = KGGenRelFact(uid=uid, type=parts[1], subject_uid=parts[2], object_uid=parts[3])
            elif uid.startswith('V') and len(parts) == 4:
                values[uid] = KGGenValFact(uid=uid, type=parts[1], subject_uid=parts[2], object_literal=parts[3])
        except Exception as e:
            continue
    return KGGen(
        domain_overview=overview,
        entities=entities,
        values=values,
        relations=relations
    )


def to_nx(kg: KGGen) -> nx.DiGraph:
    G = nx.DiGraph(
        domain_overview=kg.domain_overview,
        # x=kg
    )
    for uid, entity in kg.entities.items():
        G.add_node(
            uid,
            type=entity.type,
            canonical_name=entity.canonical_name,
            # x=entity,
        )

    for uid, val_fact in kg.values.items():
        if (subj := val_fact.subject_uid) in G.nodes:
            vf_node = f"{uid}={val_fact.object_literal}"
            G.add_node(
                vf_node,
                type=val_fact.type,
                canonical_name=val_fact.object_literal,
                # x=val_fact
            )
            G.add_edge(
                subj, vf_node,
                mode="val",
                type=val_fact.type,
                fact_uid=uid,
                # x=val_fact
            )

    for uid, rel_fact in kg.relations.items():
        if (subj_uid := rel_fact.subject_uid) in G.nodes and (obj_uid := rel_fact.object_uid) in G.nodes:
            G.add_edge(
                subj_uid, obj_uid,
                mode="rel",
                type=rel_fact.type,
                fact_uid=uid,
                # x=rel_fact
            )

    return G


def make_new_kg(e_count, r_count, v_count):
    ppt = sprompt(
        "dsgen", "kggen",
        NUM_ENTITIES=e_count,
        NUM_REL_FACTS=r_count,
        NUM_VAL_FACTS=v_count,
        NUM_CHAINS=r_count // 2,
        LANGUAGE="russian",
        DOMAIN_SPEC=sprompt("dsgen", "domain1"),
    ) + f"\n at {time.time_ns()}"
    result = llm.invoke([SystemMessage(ppt), HumanMessage("Now start generation")]).content
    result_kgd = kggen_out_parse(result)
    result_kg = to_nx(result_kgd)
    # gvis(result_kg)
    return result_kgd, result_kg

def load_kg(uid):
    return cache_iget(f"kg{uid}"), cache_iget(f"nxg{uid}")
