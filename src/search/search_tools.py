import networkx as nx
from langchain_core.tools import tool

from db.neo_base import cypher, make_gds
from db.neo_doc import *
from db.neo_kg import KType, KNode, KEntity, KFact, KRelFact, KValFact
from db.neo_rel_prop import rel_objs

embs = EmbeddingService()

"""BASE"""


@tool
def load_ontology() -> Dict[str, List[str]]:
    """
    Get existing entity and fact type codes.
    """
    logger.info("[TOOL] [ONTOLOGY]")
    return dict(
        entity_types=[i.uid for i in KType.select()],
        value_fact_types=cypher("MATCH (:KValFact)-[:K_IS]->(t:KFactType) RETURN DISTINCT(t.uid)"),
        relation_fact_types=cypher("MATCH (:KRelFact)-[:K_IS]->(t:KFactType) RETURN DISTINCT(t.uid)")
    )


@tool
def get_type_info(type_name: str) -> Dict:
    """
    By name of a type (entity of fact) return patterns of use with that type existing in db.
    """
    val_facts = cypher("""
        MATCH (n:KNode{type_code:$type})<-[SUBJ]-(f:KValFact)
        RETURN n.type_code as nt, collect(distinct(f.type_code)) as ft
    """, params=dict(type=type_name))[0][1]
    rel_facts = cypher("""
        MATCH (s:KNode)<-[SUBJ]-(f:KFact)-[OBJ]->(o:KNode)
        WHERE s.type_code in $types OR o.type_code in $types
        RETURN distinct s.type_code as st, f.type_code as ft, o.type_code as ot
    """, params=dict(types=[type_name]))
    return dict(
        type_name=type_name,
        has_value_facts=val_facts,
        has_triples=rel_facts
    )


"""ENTITIES"""


def _entity_search(q: List[str], top_k: int = 10) -> List[KEntity]:
    q = embs.embed_all(list(set(q)))
    return cypher(
        """
        UNWIND range(0, size($emb) - 1) AS idx
        CALL db.index.vector.queryNodes(
            'vector_index_KEntity_repr_embedding',
            $k,
            $emb[idx]
        ) YIELD node, score
        RETURN DISTINCT node
        """,
        dict(emb=q, k=min(max(5, top_k), 20))
    )


@tool
def entity_search(semantic_search_queries: List[str], top_k: int = 5) -> str | List[str]:
    """
    Conduct semantic vector search over entities in KG.
    You may specify any number of queries in batch (not more than 10), allowing to include different possible variants and speed up process.
    Note, that used vector index is built with embeddings over entity canonical name.
    For each input query returns top-K (not more 10 per query) entities. Returns all entities as one list.
    Choose wisely according to your task, no internal threshold applied!
    """
    if len(semantic_search_queries) > 10:
        return "Queries limit exceeded (>10)"
    logger.info(f"[TOOL] [semantic entity search] q={semantic_search_queries}")
    results = _entity_search(semantic_search_queries, top_k)
    logger.info(f"[TOOL] [semantic entity search] result count = {len(results)}")
    return [str(i) for i in results]


@tool
def describe_entities(uids: List[str]) -> str:
    """
    Fetch information on entities from database by uids (any number - this is fast batched method).
    Do not try to call this function multiple times with same input, that won't help!
    Provides:
        - entity info
        - value facts
        - entity neighborhood with relationships (1 hop only)
    """
    if not uids: return "no input given"
    entities = KEntity.select_mapped("uid", uids)
    logger.info(f"[TOOL] [entity describe] q={[str(i) for i in entities]}")
    result = ""
    for e in entities.values():
        facts = e.described_with
        v_facts = [str(i) for i in facts if isinstance(i, KValFact)]
        r_facts = [str(i) for i in [*e.described_with, *e.object_of] if isinstance(i, KRelFact)]
        result += f"{e}"
        result += "\nPROPERTIES:\n"
        result += "\n".join(v_facts)
        result += "\nNEIGHBORS:\n"
        result += "\n".join(r_facts)
        result += "\n---\n"
    return result


@tool
def describe_facts(uids: List[str]) -> str:
    """
    Fetch information on facts from database by uids (any number - this is fast batched method).
    Provides:
        - fact info, parameters
        - entity neighborhood with relationships
    Do not try to call this function multiple times with same input, that won't help!
    """
    if not uids: return "no input given"
    facts = KFact.select_mapped("uid", uids)
    logger.info(f"[TOOL] [fact describe] q={[str(i) for i in facts]}")
    result = ""
    for e in facts.values():
        facts = e.described_with
        v_facts = [str(i) for i in facts if isinstance(i, KValFact)]
        r_facts = [str(i) for i in [*e.subject, *e.objects] if isinstance(i, KRelFact)]
        result += f"{e}"
        result += "\nPROPERTIES:\n"
        result += "\n".join(v_facts)
        result += "\nNEIGHBORS:\n"
        result += "\n".join(r_facts)
        result += "\n---\n"
    return result


@tool
def entity_value_search(valfact_type_and_query: Dict[str, str]) -> Dict[str, List[Tuple[str, str]]] | str:
    """
    Search entity by known value-fact value (with fuzzy full-text search and embeddings).
    Use in case when name of entity is not known, but some characteristic is.
    Given pairs of (type code; value search sample) would return all matched facts with their subject entity.
    Conducts full-text search, and in case of no results, tries vector search which always returns top-30 without threshold and must be manually checked.
    """
    if len(valfact_type_and_query) > 10: return "count limit reached (>10)"

    def _jstr(x, prox=0):
        out = []
        for i in x:
            if prox > 0:
                words = i.split()
                out.append(" ".join([f'{j}~{prox:.2f}' for j in words]))
            else:
                out.append(f'"{i}"')
        return " OR ".join(out)

    def _output_fmt(x):
        return [(str(e), str(f)) for e, f in x]

    lucene = f'type_code:({_jstr(valfact_type_and_query.keys())}) AND value:({_jstr(valfact_type_and_query.values(), 0.5)})'
    logger.info(f"[TOOL] [full-text value search] q={lucene}")

    results = cypher(
        """
        CALL db.index.fulltext.queryNodes("value_fact_index", $query)
        YIELD node as v_fact
        MATCH (v_fact)-[:K_SUBJ]->(entity:KEntity)
        RETURN entity, v_fact
        """,
        params=dict(query=lucene)
    )
    logger.info(f"[TOOL] [full-text value search] cnt={len(results)}")

    if len(results) > 0:
        return dict(full_text_search_result=_output_fmt(results))

    q = embs.embed_all([f"{t}={v}" for t, v in valfact_type_and_query.items()])
    results = cypher(
        """
        UNWIND range(0, size($emb) - 1) AS idx
        CALL db.index.vector.queryNodes(
            'vector_index_KValFact_repr_embedding',
            $k,
            $emb[idx]
        ) YIELD node as v_fact, score
        ORDER BY score DESC
        MATCH (v_fact)-[:K_SUBJ]->(entity:KEntity)
        RETURN DISTINCT entity, v_fact
        LIMIT 30
        """,
        dict(emb=q, k=10)
    )

    logger.info(f"[TOOL] [full-text value search] fallback to vector search. cnt={len(results)}")
    return dict(full_text_search_result=_output_fmt(results))


"""TEXTS"""


@tool
def get_proofs(node_ids: List[str]) -> Dict[str, str]:
    """
    Provide proofs for given facts and mentions of entities by uids.
    This is optimal batched method - query many facts/entities at once.
    Returns map, where key is node uid, and value is a proof.
    """
    nodes = KNode.select_mapped("uid", node_ids)
    logger.info(f"[TOOL] [proofs] q={[str(i) for i in nodes]}")
    res = {}
    for uid, i in nodes.items():
        if isinstance(i, KEntity):
            m: List[Tuple[DBlock, LocatedInRel]] = rel_objs(i.mentions)
            if not m: continue
            doc = m[0][0].document.get()
            out = str(doc)
        elif isinstance(i, KFact):
            m: List[Tuple[DBlock, ProvedByRel]] = rel_objs(i.proof)
            if not m: continue
            doc = m[0][0].document.get()
            prv = m[0][1]
            out = dict(
                doc=str(doc),
                page=prv.loc_page,
                preview=prv.overview
            )
        else:
            continue
        res[uid] = out

    return res


@tool
def fallback_naive_rag(queries: List[str]) -> List[Dict]:
    """
    THIS IS LAST-RESORT METHOD, DO NOT USE UNTIL OTHER VARIANTS PRESENT!
    Do naive-rag document text chunk search based on provided queries in batch.
    Returns top-k fragments for each of input, returning only unique ones
    """
    logger.info(f"[TOOL] [naive rag] q={queries}")
    q = embs.embed_all(queries)
    results = cypher(
        """
        UNWIND range(0, size($emb) - 1) AS idx
        CALL db.index.vector.queryNodes(
            'vector_index_DChunk_repr_embedding',
            $k,
            $emb[idx]
        ) YIELD node, score
        RETURN DISTINCT node
        """,
        dict(emb=q, k=20)
    )
    logger.info(f"[TOOL] [naive rag] result count = {len(results)}")
    res = []
    for i in results:
        tb = i.text_block.get()
        doc = tb.document.get()
        loc = i.text_block.relationship(tb).loc_page
        res.append(dict(doc=doc.name, page=loc, fragment=i.repr))
    return res


"""SUBGRAPH"""


# @tool
def path_search(node_a_uid: str, node_b_uid: str, allowed_entity_types: List[str], allowed_relation_types: List[str]):
    """
    Conduct multiple k-shortest paths search between two nodes.
    You must specify which entity and fact types may be used as internal path nodes.
    Returns those paths as a subgraph.
    """
    logger.info(f"[TOOL] [path] a={node_a_uid} b={node_b_uid} aet={allowed_entity_types} art={allowed_relation_types}")
    gds = make_gds()
    source_id = gds.find_node_id(["KNode"], {"uid": node_a_uid})
    target_id = gds.find_node_id(["KNode"], {"uid": node_b_uid})
    with gds.graph.cypher.project(
            """
            MATCH
            (n:KNode)<-[r:K_SUBJ|K_OBJ]-(f:KFact)
            WHERE n.type_code in $e_typ AND f.type_code in $r_typ
            RETURN gds.graph.project(
                'tmp', f, n,
                {
                    sourceNodeLabels: labels(f),
                    targetNodeLabels: labels(n),
                    relationshipType: r.type_code
                },
                { undirectedRelationshipTypes: ['*'] }
            )
            """,
            e_typ=allowed_entity_types,
            r_typ=allowed_relation_types
    )[0] as G:
        res = gds.shortestPath.yens.stream(
            G,
            sourceNode=source_id,
            targetNode=target_id,
            k=30,
        )

        nodes = list(set(j['uid'] for i in res['path'] for j in i.nodes))
        node_data = KNode.select_mapped("uid", nodes)

        g = nx.Graph()
        g.add_nodes_from(nodes)

        logger.info(f"[TOOL] [path] cnt={len(res['path'])}")
        es = set()
        for path in res['path']:
            for vi, vj in zip(path.nodes, path.nodes[1:]):
                es.add((vi['uid'], vj['uid']))
        g.add_edges_from(list(es))

        out = "Here is resulting subgraph containing requested paths\n"

        for i in nodes:
            out += f"\nNODE\n{node_data[i]}\n"
            out += f"CONNECTED TO: {", ".join(g[i])}\n"
            out += f"END\n"

    gds.close()
    return out
