import random
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import skimage.io
import skimage.transform
import torch

PLTOPTS = {"color": "#33FFFF", "s": 15, "edgecolors": "none", "zorder": 5}

from .config import C, M
from .models import hg
from .models.line_vectorizer import LineVectorizer
from .models.multitask_learner import MultitaskHead, MultitaskLearner
from .postprocess import postprocess

cwd = Path(__file__).parent
config_file = cwd / "wireframe.yaml"

C.update(C.from_yaml(filename=config_file))
M.update(C.model)

class LCNN:
    def __init__(self, device_name, model_file: Path):
        random.seed(0)
        np.random.seed(0)
        torch.manual_seed(0)
        if torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.cuda.manual_seed(0)

        self._device = torch.device(device_name)
        checkpoint = torch.load(model_file, map_location=self._device)

        model = hg(
            depth=M.depth,
            head=lambda c_in, c_out: MultitaskHead(c_in, c_out),
            num_stacks=M.num_stacks,
            num_blocks=M.num_blocks,
            num_classes=sum(sum(M.head_size, [])),
        )
        model = MultitaskLearner(model)
        model = LineVectorizer(model)
        model.load_state_dict(checkpoint["model_state_dict"])

        self._model = model.to(self._device)
        self._model.eval()

    def __call__(self, im):
        if im.ndim == 2:
            im = np.repeat(im[:, :, None], 3, 2)
        im = im[:, :, :3]
        im_resized = skimage.transform.resize(im, (512, 512)) * 255
        image = (im_resized - M.image.mean) / M.image.stddev
        image = torch.from_numpy(np.rollaxis(image, 2)[None].copy()).float()
        with torch.no_grad():
            input_dict = {
                "image": image.to(self._device),
                "meta": [
                    {
                        "junc": torch.zeros(1, 2).to(self._device),
                        "jtyp": torch.zeros(1, dtype=torch.uint8).to(self._device),
                        "Lpos": torch.zeros(2, 2, dtype=torch.uint8).to(self._device),
                        "Lneg": torch.zeros(2, 2, dtype=torch.uint8).to(self._device),
                    }
                ],
                "target": {
                    "jmap": torch.zeros([1, 1, 128, 128]).to(self._device),
                    "joff": torch.zeros([1, 1, 2, 128, 128]).to(self._device),
                },
                "mode": "testing",
            }
            H = self._model(input_dict)["preds"]

        lines = H["lines"][0].cpu().numpy() / 128 * im.shape[:2]
        scores = H["score"][0].cpu().numpy()
        for i in range(1, len(lines)):
            if (lines[i] == lines[0]).all():
                lines = lines[:i]
                scores = scores[:i]
                break

        # postprocess lines to remove overlapped lines
        diag = (im.shape[0] ** 2 + im.shape[1] ** 2) ** 0.5
        nlines, nscores = postprocess(lines, scores, diag * 0.01, 0, False)

        return nlines, nscores
