import uuid
from dataclasses import dataclass, field

from shapely.geometry.polygon import Polygon


@dataclass
class ImageGraphNode:
    box: Polygon
    text: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4().hex))

