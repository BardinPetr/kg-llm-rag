from enum import IntEnum
from typing import List

from pydantic import BaseModel

from utils.utils import imap
from visual.models.diagram import BBox


class DetectorObjectType(IntEnum):
    NODE = 0
    ARROWHEAD = 1

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class DetectorObject(BaseModel):
    type: DetectorObjectType
    prob: float
    bbox: BBox


def parse_yolo(data) -> List[DetectorObject]:
    result = []
    data = data[0].boxes.cpu()
    for box, cls, conf in zip(data.xyxy, data.cls, data.conf):
        classifier = int(cls) % len(DetectorObjectType)
        result.append(DetectorObject(type=DetectorObjectType(classifier),
                                     prob=conf,
                                     bbox=BBox.of_xyxy(*imap(box))))
    return result
