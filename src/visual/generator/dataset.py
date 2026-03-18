import os
from pathlib import Path

import networkx as nx

from src.visual.generator.graphgen import gg_id, graphgen
from src.visual.generator.render import render_graph
from src.utils.utils import pmap

basedir = Path(os.getcwd())
basedir = basedir.parent.parent.parent
ds_dir = basedir / "dataset"
ds_img, ds_label = ds_dir / "image", ds_dir / "label"


def ds_clear():
    os.makedirs(ds_img, exist_ok=True)
    os.makedirs(ds_label, exist_ok=True)
    for i in os.listdir(ds_img):
        os.unlink(ds_img / i)
    for i in os.listdir(ds_label):
        os.unlink(ds_label / i)


def ds_one(_):
    gid = gg_id()
    img_file, label_file = ds_img / f"{gid}.png", ds_label / f"{gid}.json"
    g = nx.DiGraph()
    graphgen(g)
    label, _ = render_graph(g, img_file)
    with open(label_file, "w") as f:
        f.write(label.model_dump_json(ensure_ascii=False))


if __name__ == "__main__":
    ds_clear()
    _ = pmap(ds_one, range(1000))
