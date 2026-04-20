from typing import *

from neomodel import StructuredNode, StringProperty, IntegerProperty, ArrayProperty, FloatProperty, VectorIndex, \
    RelationshipTo, \
    ZeroOrMore, RelationshipFrom, FulltextIndex, JSONProperty
from neomodel import (
    config as neoconfig,
)
from neomodel import db as ndb

neoconfig.DATABASE_URL = f"bolt://neo4j:12345678@localhost:7687"


class KDocument(StructuredNode):
    name = StringProperty(required=True)
    metadata = JSONProperty(ensure_ascii=False)
    fragments = RelationshipFrom("KDocumentFragment", "DOC_PART_OF")


class KDocumentFragment(StructuredNode):
    document = RelationshipTo("KDocument", "DOC_PART_OF")
    title = StringProperty()
    summary = StringProperty()
    content = StringProperty()
    content_embedding = ArrayProperty(
        base_property=FloatProperty(),
        vector_index=VectorIndex(
            dimensions=4096,  # todo
            similarity_function="cosine"
        )
    )


class KMention(StructuredNode):
    fragment = RelationshipTo("KDocumentFragment", "DOC_PART_OF")
    text = StringProperty()
    offset = IntegerProperty()


class KBase(StructuredNode):
    described_by = RelationshipFrom("KFact", "DESCRIBES", cardinality=ZeroOrMore)
    describes = RelationshipFrom("KFact", "POINTS", cardinality=ZeroOrMore)
    proofs = RelationshipTo("KMention", "PROOF")


class KEntity(KBase):
    type = StringProperty(index=True, required=True)
    name = StringProperty(
        required=True,
        fulltext_index=FulltextIndex(
            analyzer="russian", eventually_consistent=False
        )
    )
    name_embedding = ArrayProperty(
        base_property=FloatProperty(),
        vector_index=VectorIndex(
            dimensions=4096,  # todo
            similarity_function="cosine"
        )
    )

    def __str__(self):
        return f"ENT:{self.type}({self.name})"

    def __repr__(self):
        return str(self)


class KFact(KBase):
    type = StringProperty(index=True, required=True)
    source = RelationshipTo("KBase", "DESCRIBES", cardinality=ZeroOrMore)
    targets = RelationshipTo("KBase", "POINTS", cardinality=ZeroOrMore)


class KRelFact(KFact):
    def __str__(self):
        return f"RFT:{self.type}"

    def __repr__(self):
        return str(self)


class KValFact(KFact):
    value = StringProperty(required=True)

    def __str__(self):
        return f"VFT:{self.type}({self.value})"

    def __repr__(self):
        return str(self)


def n_setup():
    ndb.cypher_query("MATCH (n) DETACH DELETE n")
    ndb.remove_all_labels()
    ndb.install_all_labels()


def n_cls(all=False, fact=False, entity=False):
    if all:
        ndb.cypher_query("MATCH (n) DETACH DELETE n")
    if fact:
        ndb.cypher_query("MATCH (n:KFact) DETACH DELETE n")
    if entity:
        ndb.cypher_query("MATCH (n:KEntity) DETACH DELETE n")


def cypher[T](query, params=None, type_: Type[T] = Any) -> List[T]:
    res = ndb.cypher_query(query, params or {}, resolve_objects=True)[0]
    if len(res) > 0 and len(res[0]) == 1:
        return [i[0] for i in res]
    return res
