from dataclasses import field
from typing import List, Tuple

import numpy as np
from pydantic import BaseModel

from src.visual.models.diagram import BBox


class OCRText(BaseModel):
    text: str
    bbox: BBox
    prob: float = 1.0


class OCROutput(BaseModel):
    lang: str = ""
    texts: List[OCRText] = field(default_factory=list)

    @property
    def boxes(self) -> Tuple[List[BBox], List[str]]:
        return [i.bbox for i in self.texts], [i.text for i in self.texts]
