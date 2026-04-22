from uuid import uuid4

import networkx as nx

from utils.aimodel import load_llm_lc
from workspace.extract.full.ededup.ededup import EDedupService
from workspace.extract.full.graphutils import g_nodes_of_type
from workspace.extract.full.kgextract import EntityKG, FactKG
from workspace.extract.full.neomd import *


def _names(x: Iterable[Any]) -> List[str]:
    return [i.name for i in x]


def _code_assoc[T](x: List[T]) -> Dict[str, T]:
    return {i.code: i for i in x}


llm_small = load_llm_lc("gemini2fl")
llm = load_llm_lc("gemini2")
embs = EmbeddingService()
ededup = EDedupService(embs, llm, top_k=5)


def entity_dedup_ingest(d_block: DBlock):
    d_block.refresh()
    kg: nx.DiGraph = d_block.kgg.get().content

    print("entity ingest start")

    e_nodes = g_nodes_of_type(kg, EntityKG)
    e_names = _names(e_nodes.values())
    e_keys = list(e_nodes.keys())

    entity_map = ededup.process(e_keys, e_names)  # new_id -> reuse_entity
    print(f"DEDUP LOADED ENTITIES: {len(entity_map)}")

    e_delta = {k: v
               for k, v in e_nodes.items()
               if k not in entity_map}

    print(f"NEW ENTITIES: {len(e_delta)}")

    print("generating types")
    types = {i.type for i in e_nodes.values()}
    type_map = KType.get_or_create_mapped("code", [dict(code=i) for i in types])

    print("generating embeddings")
    embeds = {k: e for k, e in zip(e_delta.keys(), embs.embed_all(_names(e_delta.values())))}

    print("ingesting entities")
    key_to_entity = [
        dict(
            code=KEntity.hash(v.name),
            type_code=v.type,
            name=v.name,
            name_embedding=embeds[k]
        )
        for k, v in e_delta.items()
    ]
    e_loaded = _code_assoc(KEntity.get_or_create(*key_to_entity))

    for k, v in e_delta.items():
        entity_map[v.uid] = e_loaded[KEntity.hash(v.name)]

    entity_map_new2old = {new.code: e_nodes[old] for old, new in entity_map.items()}

    print("ingesting entity type & prov")
    for e in e_loaded.values():
        if not e.type:
            e.type.connect(type_map[e.type_code])

        original_ent = entity_map_new2old[e.code]
        proof = {}
        if isinstance(d_block, DTxtBlock):
            proof = dict(
                loc_begin=original_ent.ref_pos,
                loc_type="char"
            )
        e.mentions.connect(d_block, properties=proof)

    d_block.kg_entity_map = {k: e.code for k, e in entity_map.items()}
    d_block.save()
    print("done")


def fact_ingest(d_block: DBlock):
    print("fact ingest start")
    d_block.refresh()
    kg: nx.DiGraph = d_block.kgg.get().content
    nodes = g_nodes_of_type(kg, FactKG)

    print("preload entities")
    entity_id_map: Dict[str, str] = d_block.kg_entity_map
    entity_map: Dict[str, KEntity] = KEntity.select_mapped("code", entity_id_map.values())
    entity_map = {int_key: entity_map[ext_key] for int_key, ext_key in entity_id_map.items()}

    print("generating types")
    types = {i.type for i in nodes.values()}
    type_map = KFactType.get_or_create_mapped("code", [dict(code=i) for i in types])

    fact_map: Dict[str, KFact] = {}
    for k, v in nodes.items():
        params = dict(
            code=do_hash(uuid4().hex),
            type_code=v.type
        )
        if v.value is not None:
            f = KValFact(
                value=str(v.value),
                **params
            )
        else:
            f = KRelFact(**params)

        f.save()
        fact_map[k] = f

        proof = {}
        if isinstance(d_block, DTxtBlock):
            proof = dict(
                overview=str(d_block.own_context)[:250],
                loc_begin=v.ref_pos,
                loc_type="char"
            )
        # TODO improve for other types
        f.proof.connect(d_block, properties=proof)

    print("ingesting fact type")
    for e in fact_map.values():
        if not e.type:
            e.type.connect(type_map[e.type_code])

    print("ingesting fact connections")
    total_map = {**fact_map, **entity_map}
    for nsi, ndi, typ in kg.edges(data="data"):
        try:
            src, dst = kg.nodes[nsi]['data'], kg.nodes[ndi]['data']
        except KeyError:
            continue

        src_n, dst_n = total_map[nsi], total_map[ndi]
        try:
            match src, typ, dst:
                case EntityKG(), "OWNS", FactKG():
                    # dst is describing src;  dst is fact, src is subject
                    dst_n.subject.connect(src_n)
                case FactKG(), "OWNS", FactKG():
                    # dst describes src;  dst is fact, src is subject
                    dst_n.subject.connect(src_n)
                case FactKG(), "POINTS", EntityKG():
                    # dst is used to describe something via src;  src is fact, dst is object
                    src_n.objects.connect(dst_n)
                case _:
                    pass
        except Exception as ex:
            print("fail:", src.uid, "->", dst.uid, "--", ex)

    d_block.save()
    print("done")


def ingest_kg_provenance(d_block: DBlock):
    pass
