import os
from enum import StrEnum
from pathlib import Path
from typing import Literal

import dotenv

dotenv.load_dotenv()

DevName = Literal["cpu", "cuda"]


class Model(StrEnum):
    LCNN = "lcnn.pth"
    NODEDETECT_YOLO = "nodedetect_y8m1.pt"

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def resolve_model(model_type: Model | str) -> Path:
    if isinstance(model_type, str) and not isinstance(model_type, StrEnum):
        model_type = Model[model_type.upper()]

    if not (models := os.getenv("MODELS_DIR_PATH", None)):
        raise ValueError("MODELS_DIR_PATH not set")

    model_env = f"MODEL_{model_type.name}"
    model_file = os.getenv(model_env, model_type.value)
    path = Path(models) / model_file
    if not path.exists() or not path.is_file():
        raise ValueError(f"Model {model_type} not found ({model_type.value} or env {model_env})")

    return path
