import time

import numpy as np
from easyocr import Reader
from ray import serve
from rich import print

from visual.analyze.ocr.model import OCROutput, OCRText
from visual.models.diagram import BBox


@serve.deployment(ray_actor_options={"num_cpus": 0.1, "num_gpus": 0.2})
class OCRReaderEasyocr:
    def __init__(self, language: str, launch_config=None, run_config=None):
        self._launch_config = launch_config or dict(
            gpu=True,
            download_enabled=False,
        )
        # TODO tune
        self._run_config = run_config or dict(
            paragraph=True,
            text_threshold=0.05,
            low_text=0.3,
            slope_ths = 0.1,
            ycenter_ths = 0.5,  # max shift y
            height_ths = 0.3,  # max box height diff
            width_ths = 0.3,  # max horizontal distance
            add_margin = 0,
            x_ths = 0.5,
            y_ths = 0.5,
            # rotation_info=[0, 90, 270]
        )
        self.language = language
        self._reader = Reader([language], **self._launch_config)
        print(f"[OCR {language}] loading")
        try:
            print(f"[OCR] loading {self.language}")
            self._reader.readtext(np.zeros((1920, 1080, 3), np.uint8))
        except:
            pass
        print(f"[OCR {language}] loading done")

    def __call__(self, image, config=None) -> OCROutput:
        print(f"[OCR] start")
        ts = time.time()
        result = self._reader.readtext(
            image,
            **{**self._run_config, **(config or {})}
        )
        result = OCROutput(
            lang=self.language,
            texts=[OCRText(text=text,
                           bbox=BBox(p1=pa, p2=pb).int())
                   for (pa, _, pb, _), text, *_ in result],
        )
        ts = time.time() - ts
        print(f"[OCR] done #{len(result.texts)} time {ts * 1000:.0f}ms")
        return result

if __name__ == "__main__":
    serve.run(OCRReaderEasyocr.bind("ru"))
