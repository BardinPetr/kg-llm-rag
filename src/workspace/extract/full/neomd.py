from typing import *

import cloudpickle
from loguru import logger
from neomodel import StructuredNode, StringProperty, ArrayProperty, FloatProperty, VectorIndex, \
    RelationshipTo as NMRT, \
    RelationshipFrom as NMRF, FulltextIndex, JSONProperty, One, IntegerProperty, StructuredRel, UniqueIdProperty, \
    RelationshipManager, ZeroOrMore, UniqueProperty
from neomodel import (
    config as neoconfig,
)
from neomodel import db as ndb
from neomodel.sync_.match import BaseSet, NodeSet

from utils.config import sys_cfg
from utils.file import do_hash
from workspace.extract.full.datastore.objstore import default_store
from workspace.extract.full.embedservice import EmbeddingService

neoconfig.DATABASE_URL = sys_cfg.n4j.conn

from typing import Any, Iterator, Optional, Protocol


class RelationshipManagerProtocol[T:StructuredNode](Protocol):
    def __str__(self) -> str: ...

    def __await__(self) -> Any: ...

    def __iter__(self) -> Iterator: ...

    def __len__(self) -> int: ...

    def __bool__(self) -> bool: ...

    def __nonzero__(self) -> bool: ...

    def __contains__(self, obj: Any) -> bool: ...

    def __getitem__(self, key: int | slice) -> Any: ...

    def check_cardinality(self, node: "StructuredNode") -> None:
        """
        Check whether a new connection to a node would violate the cardinality
        of the relationship.

        :param node: The node that is being connected.
        :raises: AttemptedCardinalityViolation
        """
        ...

    def connect(
            self, node: "StructuredNode", properties: dict[str, Any] | None = None
    ) -> "StructuredRel | None":
        """
        Connect a node.

        :param node:
        :param properties: for the new relationship
        :return: StructuredRel or None
        """
        ...

    def replace(
            self, node: "StructuredNode", properties: dict[str, Any] | None = None
    ) -> None:
        """
        Disconnect all existing nodes and connect the supplied node.

        :param node:
        :param properties: for the new relationship
        """
        ...

    def reconnect(
            self, old_node: "StructuredNode", new_node: "StructuredNode"
    ) -> None:
        """
        Disconnect old_node and connect new_node, copying over any properties
        on the original relationship.

        :param old_node:
        :param new_node:
        """
        ...

    def disconnect(self, node: "StructuredNode") -> None:
        """
        Disconnect a node.

        :param node:
        """
        ...

    def disconnect_all(self) -> None:
        """Disconnect all nodes."""
        ...

    def relationship(self, node: "StructuredNode") -> "StructuredRel | None":
        """
        Retrieve the relationship object for the first relationship between
        self and node.

        :param node:
        :return: StructuredRel or None
        """
        ...

    def all_relationships(self, node: "StructuredNode") -> "list[StructuredRel]":
        """
        Retrieve all relationship objects between self and node.

        :param node:
        :return: list[StructuredRel]
        """
        ...

    def is_connected(self, node: "StructuredNode") -> bool:
        """
        Check if a node is connected with this relationship type.

        :param node:
        :return: bool
        """
        ...

    def all(self) -> List[T]:
        """
        Return all related nodes.

        :return: list
        """
        ...

    def single(self) -> Optional[T]:
        """
        Get a single related node or None.

        :return: StructuredNode or None
        """
        ...

    def get(self, **kwargs: Any) -> T:
        """
        Retrieve a related node with the matching node properties.

        :param kwargs: same syntax as `NodeSet.filter()`
        :return: node
        """
        ...

    def get_or_none(self, **kwargs: Any) -> Optional[T]:
        """
        Retrieve a related node with the matching node properties or None.

        :param kwargs: same syntax as `NodeSet.filter()`
        :return: node or None
        """
        ...

    def filter(self, *args: Any, **kwargs: Any) -> BaseSet:
        """
        Retrieve related nodes matching the provided properties.

        :param args: a Q object
        :param kwargs: same syntax as `NodeSet.filter()`
        :return: NodeSet
        """
        ...

    def exclude(self, *args: Any, **kwargs: Any) -> BaseSet:
        """
        Exclude nodes that match the provided properties.

        :param args: a Q object
        :param kwargs: same syntax as `NodeSet.filter()`
        :return: NodeSet
        """
        ...

    def order_by(self, *props: Any) -> BaseSet:
        """
        Order related nodes by specified properties.

        :param props:
        :return: NodeSet
        """
        ...

    def match(self, **kwargs: Any) -> NodeSet:
        """
        Return set of nodes whose relationship properties match supplied args.

        :param kwargs: same syntax as `NodeSet.filter()`
        :return: NodeSet
        """
        ...


class RelationshipTo[T:StructuredNode](NMRT, RelationshipManagerProtocol[T]):
    def __init__(
            self,
            cls_name: type[T],
            relation_type: str,
            cardinality: type[RelationshipManager] = ZeroOrMore,
            model: type[StructuredRel] | None = None,
    ) -> None:
        super().__init__(
            cls_name,
            relation_type,
            cardinality,
            model
        )


class RelationshipFrom(NMRF, RelationshipManagerProtocol):
    def __init__(
            self,
            cls_name: str | type,
            relation_type: str,
            cardinality: type[RelationshipManager] = ZeroOrMore,
            model: type[StructuredRel] | None = None,
    ) -> None:
        super().__init__(
            cls_name,
            relation_type,
            cardinality,
            model
        )


class BaseNode(StructuredNode):
    # __abstract_node__ = True

    uid = UniqueIdProperty()

    @classmethod
    def iter[T](cls: T) -> Iterable[T]:
        return cls.nodes.all()

    @classmethod
    def drop_all(cls):
        for i in cls.iter():
            i.delete()

    @classmethod
    def select_uid[T](cls: T, uid: str) -> T:
        return cls.nodes.get(uid=uid)

    @classmethod
    def select[T](cls: T, **kwargs) -> List[T]:
        return list(cls.nodes.filter(**kwargs))

    @classmethod
    def get[T](cls: T, **kwargs) -> Optional[T]:
        res = list(cls.nodes.filter(**kwargs))
        return res[0] if len(res) == 1 else None


###############################


class DObject(BaseNode):
    code = StringProperty(required=True, unique_index=True)
    category = StringProperty()
    mime = StringProperty()

    refs = RelationshipFrom(BaseNode, "D_SOURCE")

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
        self.code = self.content_hash(data)
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
            code = cls.content_hash(data)
            logger.debug(f"DObject exist by content hash={code}")
            return DObject.get(code=code)


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
    loc_begin = IntegerProperty()
    loc_end = IntegerProperty()
    loc_type = StringProperty(choices=LOC_TYP)


class ProvedByRel(LocatedInRel):
    overview = StringProperty(required=True)


class MentionedInRel(LocatedInRel):
    pass


###############################

class DDocument(DEmbeddable):
    name = StringProperty(required=True)
    metadata = JSONProperty(ensure_ascii=False)

    source_file = RelationshipTo[DObject](DObject, "D_SOURCE", cardinality=One)
    docling_file = RelationshipTo[DObject](DObject, "D_DOCLING", cardinality=One)

    blocks = RelationshipFrom("DBlock", "D_IN")


class DBlock(DEmbeddable):
    title = StringProperty()
    external_context = StringProperty()
    own_context = StringProperty()
    metadata = JSONProperty()

    document = RelationshipTo[DDocument](DDocument, "D_IN", model=LocatedInRel)
    content = RelationshipTo[DObject](DObject, "D_SOURCE", cardinality=One)

    proves = RelationshipFrom("DBlock", "K_PROOF", model=ProvedByRel)


class DTxtBlock(DBlock):
    chunks = RelationshipFrom("DChunk", "D_IN")


class DImgBlock(DBlock):
    pass


class DTblBlock(DBlock):
    pass


class DChunk(DEmbeddable):
    text_block = RelationshipTo[DTxtBlock](DTxtBlock, "D_IN", model=LocatedInRel)


###############################

class KType(BaseNode):
    name = StringProperty(index=True, required=True)


class KFactType(KType):
    name = StringProperty(index=True, required=True)


###############################

class KNode(BaseNode):
    described_with = RelationshipFrom("KFact", "K_SUBJ")  # TODO


class KEntity(KNode):
    type = RelationshipTo[KType](KType, "K_IS")  # TODO
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
    mentions = RelationshipTo[DBlock](DBlock, "K_MENTION", model=MentionedInRel)  # TODO

    def __str__(self):
        return f"ENT:{self.type}({self.name})"

    def __repr__(self):
        return str(self)


class KFact(KNode):
    type = RelationshipTo[KFactType](KFactType, "K_IS")  # TODO
    proof = RelationshipTo[DBlock](DBlock, "K_PROOF", model=ProvedByRel)  # TODO
    subject = RelationshipTo[KNode](KNode, "K_SUBJ")  # TODO
    objects = RelationshipTo[KNode](KNode, "K_OBJ")


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
