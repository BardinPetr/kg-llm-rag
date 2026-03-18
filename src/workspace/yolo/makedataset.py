import os
from pathlib import Path
from random import choices

from src.utils.utils import pmap
from src.visual.models.diagram import DiagramDescription
from utils.geom import bbox_of_pts

root = Path(os.getcwd()).parent.parent.parent.parent
base_dataset = root / "dataset"
base_dataset_labels = base_dataset / "label"
base_dataset_images = base_dataset / "image"

out_dataset = Path(os.getcwd()) / "diagdataset"


def flist(x):
    return " ".join(f"{i:.5f}" for i in x)


def diag2label(x: DiagramDescription) -> str:
    res = ""

    xw,xh = x.shape

    x.normalize()
    for i in x.nodes.values():
        (cx, cy), (w, h) = i.bbox.center, i.bbox.wh
        res += f"0 {cx:.5f} {cy:.5f} {w:.5f} {h:.5f}\n"


    for e in x.edges:
        # bbox = bbox_of_pts(e.points).clip()
        # pose_pts = [
        #     i
        #     for pt in [e.points[0], e.points[-1]]
        #     for i in pt
        # ]
        # pt = " ".join(f"{i:.5f}" for i in [*bbox.center, *bbox.wh, *pose_pts])
        # res += f"1 {pt}\n"

        sz = 30 / xw, 30 / xh
        arrowhead = e.points[-1]
        res += f"2 {flist([*arrowhead, *sz])}\n"

        for seg in zip(e.points[:-1], e.points[1:]):
            edge_box = bbox_of_pts(seg)
            ccwh = [*edge_box.center, *edge_box.wh]
            res += f"1 {flist(ccwh)}\n"

    return res


def process(x):
    i, typ = x
    data = (base_dataset_labels / f"{i}.json").read_text()
    data = DiagramDescription.model_validate_json(data)
    with open(out_dataset / "labels" / typ / f"{i}.txt", "w") as f:
        f.write(diag2label(data))
    os.link(base_dataset_images / f"{i}.png", out_dataset / "images" / typ / f"{i}.png")


def clear():
    for i in ["images", "labels"]:
        for j in ["train", "val"]:
            d = (out_dataset / i / j)
            d.mkdir(parents=True, exist_ok=True)
            for f in d.iterdir():
                f.unlink()


def scan():
    tts = 0.8
    ids = [i.split('.')[0] for i in os.listdir(base_dataset_labels)]
    types = choices(["train", "val"], weights=[tts, 1 - tts], k=len(ids))
    data = list(zip(ids, types))
    pmap(process, data)


clear()
scan()
