from typing import Type, Iterable, List, Dict, Optional, Any

from graphdatascience import GraphDataScience
from neomodel import StructuredNode, UniqueIdProperty, StringProperty, db as ndb
from neomodel import (
    config as neoconfig,
)

from utils.config import sys_cfg

neoconfig.DATABASE_URL = sys_cfg.n4j.conn


class BaseNode(StructuredNode):
    __abstract_node__ = True

    @classmethod
    def iter[T](cls: Type[T]) -> Iterable[T]:
        return cls.nodes.all()

    @classmethod
    def truncate(cls):
        for i in cls.iter():
            i.delete()

    @classmethod
    def select_uid[T](cls: Type[T], uid: str) -> T:
        return cls.nodes.get(uid=uid)

    @classmethod
    def select[T](cls: Type[T], **kwargs) -> List[T]:
        return list(cls.nodes.filter(**kwargs))

    @classmethod
    def select_mapped[T, K](cls: Type[T], key: str, values: Iterable[K]) -> Dict[K, T]:
        data = cls.select(**{f"{key}__in": list(set(values))})
        return {i.__getattribute__(key): i for i in data}

    @classmethod
    def get_or_create_mapped[T, K](cls: Type[T], key: str, items: Iterable[Dict]) -> Dict[K, T]:
        data = cls.get_or_create(*items, merge_by={'keys': [key]})
        return {i.__getattribute__(key): i for i in data}

    @classmethod
    def get[T](cls: Type[T], **kwargs) -> Optional[T]:
        res = list(cls.nodes.filter(**kwargs))
        return res[0] if len(res) == 1 else None

    @classmethod
    def get_or_create[T](cls: Type[T], *items: List[Dict], **kwargs: dict[str, Any]) -> List[T]:
        return super().get_or_create(*items, **kwargs)


class IDNode(BaseNode):
    uid = UniqueIdProperty()


class CodedNode(BaseNode):
    __abstract_node__ = True
    uid = StringProperty(required=True, unique_index=True)


def n_setup():
    ndb.cypher_query("MATCH (n) DETACH DELETE n")
    ndb.remove_all_labels()
    ndb.install_all_labels()
    ndb.cypher_query("""
        CREATE FULLTEXT INDEX value_fact_index FOR (n:KValFact) ON EACH [n.value, n.type_code]
        OPTIONS { indexConfig: { `fulltext.analyzer`: 'russian' } }
    """)


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


def make_gds():
    return GraphDataScience(sys_cfg.n4j.url, auth=(sys_cfg.n4j.username, sys_cfg.n4j.password))
