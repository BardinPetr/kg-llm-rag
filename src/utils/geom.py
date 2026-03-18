import math
from typing import *

import numpy as np
from shapely import LineString, Point

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


def seg_pts(x: LineString) -> Tuple[Point, Point]:
    return ls_segments(x)[0]


def seg_np(x: LineString) -> np.ndarray:
    return np.array(x.coords)


def ls_segments(x: LineString) -> List[Tuple[Point, Point]]:
    sg = list(x.coords)
    return [tuple(Point(j) for j in i) for i in zip(sg, sg[1:])]


def ls_lines(x: LineString) -> List[LineString]:
    sg = list(x.coords)
    return [LineString(i) for i in zip(sg, sg[1:])]


def m_angle(x: Tuple[Point, Point], y: Tuple[Point, Point]) -> float:
    """
    pi ccw
    -pi cw
    """
    dx = x[1].x - x[0].x
    dy = x[1].y - x[0].y
    dx2 = y[1].x - y[0].x
    dy2 = y[1].y - y[0].y
    angle_x = math.atan2(dy, dx)
    angle_y = math.atan2(dy2, dx2)
    angle_diff = angle_y - angle_x
    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    while angle_diff < -math.pi:
        angle_diff += 2 * math.pi
    return angle_diff
