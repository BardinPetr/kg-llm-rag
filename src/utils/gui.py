import random
from typing import Tuple, List

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from more_itertools import flatten
from shapely import LineString, Point

from src.utils.utils import imap
from src.visual.models.diagram import BBox


def vis(x, **kwargs):
    plt.figure(figsize=(16, 16))
    plt.imshow(x, **{'cmap': 'hot', **kwargs})


def to_rgb(x):
    if len(x.shape) == 3 and x.shape[-1] == 3:
        return x
    return cv2.cvtColor(x, cv2.COLOR_GRAY2BGR)


def vic(x, y, **kwargs):
    fig, axes = plt.subplots(1, 2, figsize=(20, 16))
    axes[0].imshow(x, **{'cmap': 'hot' if len(x.shape) == 2 else None, **kwargs})
    axes[1].imshow(y, **{'cmap': 'hot' if len(y.shape) == 2 else None, **kwargs})
    plt.tight_layout()
    plt.show()


def vbbox(orig, bboxes, annotations=None, color=(0, 255, 0), is_xywh=False):
    try:
        im = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    except:
        im = cv2.cvtColor(orig, cv2.COLOR_GRAY2BGR)
    pts = []
    for i in bboxes:
        if isinstance(i, BBox):
            i = i.xywh
            is_xywh = True
        x = imap(flatten([i]))
        if is_xywh:
            x = (x[0], x[1], x[0] + x[2], x[1] + x[3])
        pts.append(x[:2])
        cv2.rectangle(im, x[:2], x[2:], color, 2)

    if annotations:
        for txt, pt in zip(annotations, pts):
            cv2.putText(im, txt, pt, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    return im


cmap = plt.get_cmap("jet")
norm = matplotlib.colors.Normalize(vmin=0, vmax=1)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])


def color_range_01(x: float = None) -> Tuple[int, int, int]:
    if x is None: x = random.random()
    return [int(i * 255) for i in sm.to_rgba(x)[:3]]


def stack_images(images, cols, rows):
    h, w = images[0].shape[:2]
    resized_images = []
    for img in images[:cols * rows]:
        if img.shape[:2] != (h, w):
            img = cv2.resize(img, (w, h))
        resized_images.append(img)
    image_rows = []
    for i in range(rows):
        start_idx = i * cols
        end_idx = start_idx + cols
        row_images = resized_images[start_idx:end_idx]
        row = np.hstack(row_images)
        image_rows.append(row)
    stacked = np.vstack(image_rows)
    return stacked


def to_rgb_or_copy(img):
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return img.copy()


def vis_pts(img, pts, xy_rev=False, circ=True, csize=3, col=(255, 0, 0)):
    res_vis = to_rgb_or_copy(img)
    for i in pts:
        pt = imap(i[::-1] if xy_rev else i)
        if circ:
            cv2.circle(res_vis, pt, csize, col, 1)
        else:
            x, y = pt
            res_vis[y, x] = col
    return res_vis


def vis_lines(img, lines, yx=False) -> np.ndarray:
    result = to_rgb_or_copy(img)
    for line in lines:
        if yx:
            y1, x1, y2, x2 = line
        else:
            x1, y1, x2, y2 = line
        cv2.line(result, (x1, y1), (x2, y2), color_range_01(random.random()), 1)
        cv2.circle(result, (x1, y1), 5, (255, 0, 0), 1)
        cv2.circle(result, (x2, y2), 5, (0, 0, 255), 1)
    return result


def vis_ls(img, lines: List[LineString], thick=1) -> np.ndarray:
    result = to_rgb_or_copy(img)
    for line in lines:
        segs = list(line.coords)
        col = color_range_01(random.random())
        cv2.circle(result, imap(segs[0]), 5, (255, 0, 0), thick)
        for p0, p1 in zip(segs, segs[1:]):
            cv2.line(result, imap(p0), imap(p1), col, 1)
            cv2.circle(result, imap(p1), 5, (0, 255, 0), thick)
        cv2.circle(result, imap(segs[-1]), 5, (0, 0, 255), thick)
    return result


def pt_c(x: Point) -> Tuple[int, int]:
    return imap(list(x.coords[0]))


def vis_arrow(img, a: Point, b: Point, col=(0, 255, 0), thick=1):
    cv2.arrowedLine(img, pt_c(a), pt_c(b), col, thick)


def vis_circ(img, a: Point, col=(0, 255, 0), rad=5, thick=1):
    cv2.circle(img, pt_c(a), rad, col, thick)
