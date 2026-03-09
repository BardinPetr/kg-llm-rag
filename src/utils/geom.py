from typing import *

import numpy as np

from visual.models.diagram import BBox, num

NA = lambda x: np.array(x)

def bbox_union(bboxes: List[BBox]) -> BBox:
    x_min = bboxes[0].p1[0]
    y_min = bboxes[0].p1[1]
    x_max = bboxes[0].p2[0]
    y_max = bboxes[0].p2[1]
    for bbox in bboxes[1:]:
        x_min = min(x_min, bbox.p1[0])
        y_min = min(y_min, bbox.p1[1])
        x_max = max(x_max, bbox.p2[0])
        y_max = max(y_max, bbox.p2[1])
    return BBox(p1=(x_min, y_min), p2=(x_max, y_max))


def bbox_pad(bbox: BBox, pad_pct: float) -> BBox:
    pad_x = bbox.wh[0] * pad_pct
    pad_y = bbox.wh[1] * pad_pct
    x_min = bbox.p1[0] - pad_x
    y_min = bbox.p1[1] - pad_y
    x_max = bbox.p2[0] + pad_x
    y_max = bbox.p2[1] + pad_y
    return BBox(p1=(x_min, y_min), p2=(x_max, y_max))


def bbox_of_pts(pts: List[Tuple[num, num]], pad=0) -> BBox:
    x_coords = [x for x, y in pts]
    y_coords = [y for x, y in pts]
    bbox = BBox(p1=(min(x_coords), min(y_coords)), p2=(max(x_coords), max(y_coords)))
    bbox = bbox_pad(bbox, pad)
    return bbox
