from typing import *

import cloudpickle
from neomodel import StructuredNode, StringProperty, ArrayProperty, FloatProperty, VectorIndex, \
    RelationshipTo, \
    RelationshipFrom, FulltextIndex, JSONProperty, One, IntegerProperty, StructuredRel
from neomodel import (
    config as neoconfig,
)
from neomodel import db as ndb

from utils.config import sys_cfg
from utils.file import do_hash
from workspace.extract.full.datastore.objstore import default_store
from workspace.extract.full.embedservice import EmbeddingService

neoconfig.DATABASE_URL = sys_cfg.n4j.conn


class BaseNode(StructuredNode):
    __abstract_node__ = True

    @classmethod
    def iter[T](cls: T) -> Iterable[T]:
        return cls.nodes.all()

    @classmethod
    def drop_all(cls):
        for i in cls.iter():
            i.delete()

    @classmethod
    def select_by_id[T](cls: T, uid) -> List[T]:
        return list(cls.nodes.filter(element_id=uid))

    @classmethod
    def select[T](cls: T, **kwargs) -> List[T]:
        return list(cls.nodes.filter(**kwargs))


###############################


class DObject(BaseNode):
    code = StringProperty(required=True, unique_index=True)
    category = StringProperty()
    mime = StringProperty()

    _content_tmp: Optional[bytes] = None

    @property
    def obj_ref(self) -> Tuple[str, str]:
        return str(self.category), str(self.code)

    @property
    def content(self) -> Optional[Any]:
        if data := default_store.load(*self.obj_ref):
            return cloudpickle.loads(data)
        return None

    @content.setter
    def content(self, data: Any):
        byte_data = cloudpickle.dumps(data)
        self.code = do_hash(byte_data)
        self._content_tmp = byte_data

    def pre_save(self):
        assert self._content_tmp is not None

    def post_save(self):
        assert self._content_tmp is not None
        default_store.store(*self.obj_ref, self._content_tmp)

    def pre_delete(self):
        default_store.delete(*self.obj_ref)


###############################

class DEmbeddable(BaseNode):
    repr = StringProperty()
    repr_embedding = ArrayProperty(
        base_property=FloatProperty(),
        vector_index=VectorIndex(
            dimensions=EmbeddingService.MX_SZ,
            similarity_function="cosine"
        )
    )


###############################

class LocatedInRel(StructuredRel):
    LOC_TYP = {"char": "char", "dloc": "dloc"}
    loc_begin = IntegerProperty(required=True)
    loc_end = IntegerProperty(required=True)
    loc_type = StringProperty(choices=LOC_TYP)


class ProvedByRel(LocatedInRel):
    overview = StringProperty(required=True)


class MentionedInRel(LocatedInRel):
    pass


###############################

class DDocument(DEmbeddable):
    name = StringProperty(required=True)
    metadata = JSONProperty(ensure_ascii=False)

    source_file = RelationshipTo(DObject, "D_SOURCE", cardinality=One)
    docling_file = RelationshipTo(DObject, "D_DOCLING", cardinality=One)

    blocks = RelationshipFrom("DDocumentBlock", "D_IN")


class DBlock(DEmbeddable):
    title = StringProperty()
    external_context = StringProperty()
    own_context = StringProperty()

    document = RelationshipTo(DDocument, "D_IN", model=LocatedInRel)
    content = RelationshipTo(DObject, "D_CONTENT", cardinality=One)

    proves = RelationshipFrom("DBlock", "K_PROOF", model=ProvedByRel)


class DTxtBlock(DBlock):
    chunks = RelationshipFrom("DChunk", "D_IN")


class DImgBlock(DBlock):
    pass


class DTblBlock(DBlock):
    pass


class DChunk(DEmbeddable):
    text_block = RelationshipTo(DTxtBlock, "D_IN", model=LocatedInRel)


###############################

class KType(BaseNode):
    name = StringProperty(index=True, required=True)


class KFactType(KType):
    name = StringProperty(index=True, required=True)


###############################

class KNode(BaseNode):
    described_with = RelationshipFrom("KFact", "K_SUBJ")  # TODO


class KEntity(KNode):
    type = RelationshipTo(KType, "K_IS")  # TODO
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
    mentions = RelationshipTo("KMention", "K_MENTION", model=MentionedInRel)  # TODO

    def __str__(self):
        return f"ENT:{self.type}({self.name})"

    def __repr__(self):
        return str(self)


class KFact(KNode):
    type = RelationshipTo(KFactType, "K_IS")  # TODO
    proof = RelationshipTo(DBlock, "K_PROOF", model=ProvedByRel)  # TODO
    subject = RelationshipTo(KNode, "K_SUBJ")  # TODO
    objects = RelationshipTo(KNode, "K_OBJ")


class KRelFact(KFact):
    def __str__(self):
        return f"RFT:{self.type}"

    def __repr__(self):
        return str(self)


class KValFact(KFact):
    value = StringProperty(required=True)  # TODO
    unit = StringProperty()

    def __str__(self):
        return f"VFT:{self.type}({self.value})"

    def __repr__(self):
        return str(self)


###############################


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
