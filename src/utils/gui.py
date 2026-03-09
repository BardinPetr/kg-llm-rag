from typing import Tuple

import cv2
import matplotlib
import matplotlib.pyplot as plt
from more_itertools import flatten

from utils.utils import imap
from visual.models.diagram import BBox


def vis(x):
    plt.figure(figsize=(12, 12))
    plt.imshow(x, cmap='hot')


def vic(x, y):
    fig, axes = plt.subplots(1, 2, figsize=(20, 12))
    axes[0].imshow(x, cmap='hot' if len(x.shape) == 2 else None)
    axes[1].imshow(y, cmap='hot' if len(y.shape) == 2 else None)
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
            print(i)
            i = i.xywh
            is_xywh = True
        x = imap(flatten([i]))
        if is_xywh:
            x = (x[0], x[1], x[0] + x[2], x[1] + x[3])
        pts.append(x[:2])
        cv2.rectangle(im, x[:2], x[2:], color, 2)

    if annotations:
        for txt, pt in zip(annotations, pts):
            print(txt, pt)
            cv2.putText(im, txt, pt, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    return im


cmap = plt.get_cmap("jet")
norm = matplotlib.colors.Normalize(vmin=0, vmax=1)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

def color(x: float) -> Tuple[int, int, int]:
    return [int(i * 255) for i in sm.to_rgba(x)[:3]]

