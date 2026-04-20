import networkx as nx
from docling_core.types import DoclingDocument

from utils.aimodel import load_llm_lc
from workspace.extract.full.ededup.ededup import EDedupService
from workspace.extract.full.embedservice import EmbeddingService
from workspace.extract.full.graphutils import g_nodes_of_type
from workspace.extract.full.kgextract import doc_extract_kg, EntityKG, FactKG
from workspace.extract.full.neomd import *


def _names(x: Iterable[Any]) -> List[str]:
    return [i.name for i in x]


class KGLoader:

    def __init__(self,
                 embs: EmbeddingService,
                 document: DoclingDocument):
        self._llm_small = load_llm_lc("gemini2fl")
        self._llm = load_llm_lc("gemini2fl")

        self._ededup = EDedupService(embs, self._llm_small, top_k=5)

        self._embs = embs
        self._ddoc = document
        self._doc_txt = self._ddoc.export_to_markdown()

        self._kdoc: KDocument = None
        self._kg: nx.DiGraph = None

        # entity internal id -> KGEntity
        self._entity_map = {}
        # entity internal id -> KGFact
        self._fact_map = {}

    def make_base_doc(self):
        self._kdoc = KDocument(name=self._ddoc.name)
        self._kdoc.save()

    def make_kg(self):
        self._kg = doc_extract_kg(self._llm, self._doc_txt)

    def ingest_entities(self):
        e_nodes = g_nodes_of_type(self._kg, EntityKG)
        e_names = _names(e_nodes.values())
        e_keys = list(e_nodes.keys())

        self._entity_map = self._ededup.process(e_keys, e_names)  # new_id -> reuse_entity
        print(f"DEDUP LOADED ENTITIES: {len(self._entity_map)}")

        e_delta = {k: v
                   for k, v in e_nodes.items()
                   if k not in self._entity_map}
        print(f"NEW ENTITIES: {len(e_delta)}")

        embeds = {k: e for k, e in zip(e_delta.keys(), self._embs.embed_all(_names(e_delta.values())))}

        for k, v in e_delta.items():
            e = KEntity(
                type=v.type,
                name=v.name,
                name_embedding=embeds[k]
            )

            e.save()
            self._entity_map[v.uid] = e

    def ingest_facts(self):
        nodes = g_nodes_of_type(self._kg, FactKG)

        for k, v in nodes.items():
            params = dict(
                type=v.type
            )
            if v.value is not None:
                f = KValFact(
                    value=str(v.value),
                    **params
                )
            else:
                f = KRelFact(**params)

            f.save()
            self._fact_map[k] = f

        total_map = {**self._fact_map, **self._entity_map}

        for nsi, ndi, typ in self._kg.edges(data="data"):
            try:
                src, dst = self._kg.nodes[nsi]['data'], self._kg.nodes[ndi]['data']
            except KeyError:
                continue

            src_n, dst_n = total_map[nsi], total_map[ndi]
            try:
                match src, dst, typ:
                    case EntityKG(), FactKG(), "OWNS":
                        dst_n.source.connect(src_n)
                    case FactKG(), EntityKG(), "POINTS":
                        src_n.source.connect(dst_n)
                    case FactKG(), FactKG(), "OWNS":
                        src_n.targets.connect(dst_n)
                    case _:
                        pass
            except Exception as ex:
                print("fail:", src.uid, "->", dst.uid, "--", ex)

    # TODO
    def encode_proof(self, doc_pos):
        m = KMention(

        )
        m.save()
        return m

    # TODO
    def ingest_docstrutcure(self):
        pass
