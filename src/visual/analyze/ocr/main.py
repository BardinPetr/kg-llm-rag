from ray import serve

from model import OCROutput


@serve.deployment(ray_actor_options={})
class OCRSolver:
    def __init__(self):
        pass

    def __call__(self, image, prefer_lang=None) -> OCROutput:
        pass
