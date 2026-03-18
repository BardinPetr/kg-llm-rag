from collections import Counter
from typing import List, Dict

import cv2
from ray import serve
from ultralytics import YOLO

from utils.models import resolve_model, Model, DevName
from visual.analyze.detection.model import DetectorObject, parse_yolo, DetectorObjectType

DETECTOR_THRESHOLD = {
    DetectorObjectType.NODE: 0.5,
    DetectorObjectType.ARROWHEAD: 0.2
}

DETECTOR_MIN_SIZE = {
    DetectorObjectType.NODE: 3000,
    DetectorObjectType.ARROWHEAD: 30
}


@serve.deployment(ray_actor_options={"num_cpus": 1})
class DiagramNodesDetector:
    def __init__(self, device: DevName = "cpu", config: Dict = None):
        self._config = config or dict(conf=0.1, iou=0.4, imgsz=640)
        print(f"[YOLO-DIAG] loading")
        self._device = device
        self._model = YOLO(resolve_model(Model.NODEDETECT_YOLO))
        print(f"[YOLO-DIAG] loading done")

    def _run(self, image):
        if self._device != "cpu":
            image = image.to_device(self._device)
        return self._model(image, device=self._device, **self._config)

    def __call__(self, image) -> List[DetectorObject]:
        print("[YOLO-DIAG] Running")
        result = self._run(image)
        result = parse_yolo(result)
        result = [i
                  for i in result
                  if i.prob > DETECTOR_THRESHOLD[i.type]
                    and i.bbox.area > DETECTOR_MIN_SIZE[i.type]]
        stats = Counter([i.type for i in result])
        print(f"[YOLO-DIAG] Detections: {stats.items()}")
        return result


if __name__ == "__main__":
    a = serve.run(DiagramNodesDetector.bind())
    # orig = cv2.imread(f"/home/petr/study/diploma/src/datasetgen/demo/044030790.png")
    # res = a.remote(orig).result()
    # a(orig)
    # print(res)
