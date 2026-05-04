from enum import StrEnum
from typing import *
from typing import Any, Optional

import cloudpickle
from loguru import logger
from neomodel import StringProperty, ArrayProperty, FloatProperty, VectorIndex, \
    JSONProperty, One, IntegerProperty, StructuredRel, UniqueProperty

from utils.file import do_hash
from service.embedservice import EmbeddingService
from db.store.objstore import default_store
from db.neo_base import BaseNode, IDNode, CodedNode
from db.neo_rel_prop import RelationshipTo, RelationshipFrom



class DEmbeddable(BaseNode):
    repr = StringProperty()
    repr_embedding = ArrayProperty(
        base_property=FloatProperty(),
        vector_index=VectorIndex(
            dimensions=EmbeddingService.MX_SZ,
            similarity_function="cosine"
        )
    )

    def __str__(self):
        return f"TXT({self.repr[:20]}...)"

    def __repr__(self):
        return str(self)

###############################


class DObject(CodedNode):
    category = StringProperty()
    mime = StringProperty()

    refs = RelationshipFrom(IDNode, "D_SOURCE")

    _content_tmp: Optional[bytes] = None

    @property
    def obj_ref(self) -> Tuple[str, str]:
        return str(self.category), str(self.uid)

    @property
    def content(self) -> Optional[Any]:
        if data := default_store.load(*self.obj_ref):
            return cloudpickle.loads(data)
        return None

    @content.setter
    def content(self, data: Any):
        byte_data = cloudpickle.dumps(data)
        self.uid = self.content_hash(data)
        self._content_tmp = byte_data

    def pre_save(self):
        assert self._content_tmp is not None

    def post_save(self):
        assert self._content_tmp is not None
        default_store.store(*self.obj_ref, self._content_tmp)

    def pre_delete(self):
        default_store.delete(*self.obj_ref)

    @classmethod
    def content_hash(cls, data) -> str:
        return do_hash(cloudpickle.dumps(data))

    @classmethod
    def make(cls, data) -> 'DObject':
        doc_file = DObject()
        doc_file.content = data
        try:
            return doc_file.save()
        except UniqueProperty:
            uid = cls.content_hash(data)
            logger.debug(f"DObject exist by content hash={uid}")
            return DObject.get(uid=uid)


###############################

class LocatedInRel(StructuredRel):
    LOC_TYP = {"char": "char", "line": "line", "page": "page"}
    loc_page = IntegerProperty()
    loc_begin = IntegerProperty()
    loc_end = IntegerProperty()
    loc_type = StringProperty(choices=LOC_TYP)
    loc_bind = StringProperty()
    loc_didx = StringProperty()
    loc_drefs = ArrayProperty()

    def __str__(self):
        return f"PROV_REL(p={self.loc_page},{self.loc_begin}-{self.loc_end},d={self.loc_didx})"

    def __repr__(self):
        return str(self)

class ProvedByRel(LocatedInRel):
    overview = StringProperty()

    def __str__(self):
        return f"PROV_REL(p={self.loc_page},{self.loc_begin}-{self.loc_end},d={self.loc_didx},`{self.overview[:20]}`...)"

class MentionedInRel(LocatedInRel):
    pass


###############################

class DocumentProcStages(StrEnum):
    FILE = "FILE"
    DOCL = "DOCL"
    TEXT = "TEXT"
    TABL = "TABL"
    IMAG = "IMAG"
    NXKG = "NXKG"
    KGEE = "KGEE"
    KGRE = "KGRE"


class BlockProcStages(StrEnum):
    LOAD = "LOAD"
    NXKG = "NXKG"
    KGIE = "KGIE"
    KGIR = "KGIR"


###############################


class DDocument(IDNode, DEmbeddable):
    name = StringProperty(required=True)
    metadata = JSONProperty(ensure_ascii=False)
    stages = ArrayProperty()

    source_file = RelationshipTo[DObject](DObject, "D_SOURCE", cardinality=One)
    docling_file = RelationshipTo[DObject](DObject, "D_DOCLING", cardinality=One)

    blocks = RelationshipFrom("DBlock", "D_IN")

    def __str__(self):
        return f"DOC(`{self.name}`)"


class DBlock(IDNode, DEmbeddable):
    title = StringProperty()
    external_context = StringProperty()
    own_context = StringProperty()
    metadata = JSONProperty()

    document = RelationshipTo[DDocument](DDocument, "D_IN", model=LocatedInRel)
    content = RelationshipTo[DObject](DObject, "D_SOURCE", cardinality=One)
    kgg = RelationshipTo[DObject](DObject, "D_NX", cardinality=One)
    kg_entity_map = JSONProperty()

    stages = ArrayProperty()

    proves = RelationshipFrom("DBlock", "K_PROOF", model=ProvedByRel)

    def __str__(self):
        return f"BLK(`{self.title}`)"


class DTxtBlock(DBlock):
    chunks = RelationshipFrom("DChunk", "D_IN")


class DImgBlock(DBlock):
    pass


class DTblBlock(DBlock):
    pass


class DExcelBlock(DBlock):
    pass


class DChunk(IDNode, DEmbeddable):
    text_block = RelationshipTo[DTxtBlock](DTxtBlock, "D_IN", model=LocatedInRel)

