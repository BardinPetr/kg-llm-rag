from typing import *


def g_nodes(g) -> List[Any]:
    return g.nodes(data="data")


def g_nodes_of_type[T](g, typ: Type[T]) -> Dict[str, T]:
    return {k: v for k, v in g_nodes(g) if isinstance(v, typ)}
