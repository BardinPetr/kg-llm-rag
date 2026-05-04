from typing import Protocol, Any, Iterator, List, Optional, Dict

from neomodel import StructuredNode, StructuredRel, NodeSet
from neomodel.sync_.match import BaseSet


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
