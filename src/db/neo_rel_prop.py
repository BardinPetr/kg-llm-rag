from typing import *

from neomodel import StructuredNode, RelationshipTo as NMRT, RelationshipManager, ZeroOrMore, StructuredRel, \
    RelationshipFrom as NMRF

from db.neo_rel_manager import RelationshipManagerProtocol


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


def rel_objs[T:StructuredNode](rel: RelationshipTo[T]) -> List[Tuple[T, StructuredRel]]:
    data = rel.all()
    return [(i, rel.relationship(i)) for i in data]
