import random

import cv2
import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from ray import serve
from rich import print

from utils.models import resolve_model, Model
from visual.analyze.structure.lcnn.inference import LCNN

cmap = plt.get_cmap("jet")
norm = mpl.colors.Normalize(vmin=0, vmax=1)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])


def c(x):
    return [int(i * 255) for i in sm.to_rgba(x)[:3]]


@serve.deployment(ray_actor_options={"num_cpus": 1, "num_gpus": 0.2})
class DiagramGraphExtractor:
    def __init__(self, device="cuda"):
        print(f"[LCNN] loading")
        self._model = LCNN(device, resolve_model(Model.LCNN))
        print(f"[LCNN] loading done")

    def __call__(self, image, threshold=0.9):
        nlines, nscores = self._model(image)
        out = np.zeros_like(image)
        # out = im[:]
        for (a, b), s in zip(nlines, nscores):
            if s < threshold: continue
            pt1 = (int(a[1]), int(a[0]))
            pt2 = (int(b[1]), int(b[0]))
            cv2.line(out, pt1, pt2, c(random.random()), 5)
            # cv2.line(out, pt1, pt2, (0, 0, 255), 5)
            cv2.circle(out, pt1, 7, (0, 255, 0), -1)
            cv2.circle(out, pt2, 7, (255, 0, 0), -1)
        return out


if __name__ == "__main__":
    # a = DiagramGraphExtractor()
    a = serve.run(DiagramGraphExtractor.bind())

    orig = cv2.imread(f"/home/petr/study/diploma/src/datasetgen/demo/044030790.png")
    r = a.remote(orig).result()
    # r = a(orig)

    print(r)