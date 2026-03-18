from typing import *

import shapely
from pydantic import BaseModel, model_serializer, Field, model_validator

from utils.utils import *

type num = int | float


class BBox(BaseModel):
    p1: Tuple[num, num] # left up
    p2: Tuple[num, num] # right down

    @classmethod
    def of_xywh(cls, x, y, w, h):
        return BBox(p1=imap([x, y]), p2=imap([x + w, y + h]))

    @classmethod
    def of_xyxy(cls, x, y, x1, y1):
        return BBox(p1=[x, y], p2=[x1, y1])

    @classmethod
    def of_cxcywh(cls, cx, cy, w, h):
        x, y = cx - w / 2, cy - h / 2
        return cls.of_xywh(x, y, w, h)

    @model_serializer
    def serialize_model(self) -> list[num]:
        return [self.p1[0], self.p1[1], self.p2[0], self.p2[1]]

    @model_validator(mode='before')
    @classmethod
    def deserialize(cls, data: Any):
        if isinstance(data, list | tuple) and len(data) == 4:
            x1, y1, x2, y2 = [int(i) for i in data]
            return dict(p1=(x1, y1), p2=(x2, y2))
        return data

    @property
    def center(self) -> Tuple[num, num]:
        return (self.p1[0] + self.p2[0]) / 2, (self.p1[1] + self.p2[1]) / 2

    @property
    def wh(self) -> Tuple[num, num]:
        return self.p2[0] - self.p1[0], self.p2[1] - self.p1[1]

    @property
    def xywh(self):
        return *self.p1, *self.wh

    @property
    def xyxy(self):
        return *self.p1, *self.p2

    @property
    def area(self):
        w, h = self.wh
        return w * h

    def clip(self, width=1, height=1) -> "BBox":
        return BBox(p1=(max(0, min(self.p1[0], width)), max(0, min(self.p1[1], height))),
                    p2=(max(0, min(self.p2[0], width)), max(0, min(self.p2[1], height))))

    def mul(self, x, y):
        return BBox(p1=(self.p1[0] * x, self.p1[1] * y),
                    p2=(self.p2[0] * x, self.p2[1] * y))

    def int(self):
        return BBox(p1=imap(self.p1), p2=imap(self.p2))

    def bbox_pad(self, pad_pct: float) -> "BBox":
        pad_x = self.wh[0] * pad_pct
        pad_y = self.wh[1] * pad_pct
        return BBox(p1=(self.p1[0] - pad_x, self.p1[1] - pad_y), p2=(self.p2[0] + pad_x, self.p2[1] + pad_y))

    def polygon(self):
        return shapely.box(*self.xyxy)

    @classmethod
    def of_polygon(cls, poly):
        minx, miny, maxx, maxy = poly.bounds
        return cls.of_xyxy(minx, miny, maxx, maxy)

class LineSeg(BaseModel):
    p1: Tuple[num, num]
    p2: Tuple[num, num]



def bbox_from_list(x):
    if isinstance(x, list | tuple):
        print(x)
        x1, y1, x2, y2 = [int(i) for i in x]
        return BBox(p1=(x1, y1), p2=(x2, y2))
    print("&", type(x), x)
    return x


class DiagramNode(BaseModel):
    id: str
    bbox: BBox
    # bbox: Annotated[BBox, PlainValidator(bbox_from_list)]
    label: str = ""
    type: Optional[str] = None
    props: Dict = Field(default_factory=dict)


class DiagramEdge(BaseModel):
    src_id: str
    dst_id: str
    points: List[Tuple[num, num]]
    arrowhead: Optional[Tuple[num, num]] = None
    directed: bool = True
    label: str = ""
    type: Optional[str] = None
    props: Dict = Field(default_factory=dict)


class DiagramDescription(BaseModel):
    nodes: Dict[str, DiagramNode] = Field(default_factory=dict)
    edges: List[DiagramEdge] = Field(default_factory=list)
    shape: Tuple[num, num]
    image_code: str = ""

    def normalize(self):
        for i in self.nodes.values():
            i.bbox = BBox(p1=zdiv(i.bbox.p1, self.shape), p2=zdiv(i.bbox.p2, self.shape))
        for i in self.edges:
            i.points = [zdiv(i, self.shape) for i in i.points]
