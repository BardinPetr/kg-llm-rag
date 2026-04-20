from utils.prompt import sprompt, uprompt
from workspace.extract.full.neomd import KValFact, KEntity, cypher
from .model import *


def _make_facts(e: KEntity):
    data = {i.type: i.value
            for i in e.described_by
            if isinstance(i, KValFact)}
    return json.dumps(data, ensure_ascii=False)


def _make_tasks(input_queries, variants: Dict[str, List[KEntity]]) -> EDedupTasks:
    return EDedupTasks(tasks=[
        EDedupTask(
            target_uid=str(trg_uid),
            target=str(target),
            options=[
                EDedupTaskOption(
                    uid=opt_ent.element_id,
                    variant=str(opt_ent),
                    facts=_make_facts(opt_ent)
                )
                for opt_ent in opts
            ]
        )
        for (trg_uid, target), opts in zip(enumerate(input_queries), variants.values())
    ])


class EDedupService:
    def __init__(self, embedding_service, model, top_k=5):
        self._model = model.with_structured_output(EDedupResults)
        self._embs = embedding_service
        self._top_k = top_k

    def process(self, input_ids: List[str], input_queries: List[str]) -> Dict[str, KEntity]:
        variants = self._select_nearest(input_queries)
        all_items = {i.element_id: i for opts in variants.values() for i in opts}
        edi = _make_tasks(input_queries, variants).model_dump()

        output: List[EDedupResult] = self._model.invoke([
            ("system", sprompt("kge", "ededup")),
            ("user", uprompt("kge", "ededup", input_data=edi))
        ]).results

        reused = {
            input_ids[int(i.target_uid)]: match
            for i in output
            if (match := all_items.get(i.matched_option_uid)) and
               i.confidence in {EDedupConfidence.EXACT, EDedupConfidence.HIGH}
        }

        print(f"DEDUP RES: reuse={len(reused)} dropped={len(output) - len(reused)} all={len(input_queries)}")
        return reused

    def _select_nearest(self, input_queries: List[str]) -> Dict[str, List[KEntity]]:
        q_embeddings = self._embs.embed_all(input_queries)
        variants: List[Tuple[str, KEntity, List[KValFact]]] = cypher(
            """
            UNWIND range(0, size($emb) - 1) AS idx
    
            CALL db.index.vector.queryNodes(
                'vector_index_KEntity_name_embedding',
                $k,
                $emb[idx]
            ) YIELD node, score
    
            RETURN idx, COLLECT(node) as opts
            """,
            dict(emb=q_embeddings, k=self._top_k)
        )
        return {k: row for k, row in variants}
