import random

import cv2
import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from ray import serve
from rich import print

@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class DiagramGraphExtractor:
    def __init__(self):
        print(f"[LCNN] loading")
        print(f"[LCNN] loading done")

    def __call__(self, image, threshold=0.9):
        return None


if __name__ == "__main__":
    # a = DiagramGraphExtractor()
    a = serve.run(DiagramGraphExtractor.bind())

    orig = cv2.imread(f"/home/petr/study/diploma/src/datasetgen/demo/044030790.png")
    r = a.remote(orig).result()
    # r = a(orig)

    print(r)