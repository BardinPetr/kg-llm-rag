import os
from base64 import b64encode
from typing import Optional

import aiohttp
import cv2
import dotenv
from ray import serve

from visual.analyze.ocr.model import OCROutput, OCRText
from visual.models.diagram import BBox


def cv2_to_b64png(x, compression: int = 9) -> str:
    success, buffer = cv2.imencode('.png', x, [cv2.IMWRITE_PNG_COMPRESSION, compression])
    if not success:
        raise RuntimeError("Failed to encode image as PNG")
    return b64encode(buffer).decode('utf-8')


def decode_response(data) -> OCROutput:
    blocks = (data
              .get("result", {})
              .get("textAnnotation", {})
              .get("blocks", []))
    lang = ""
    for block in blocks:
        languages = block.get("languages", [])
        if languages:
            lang = languages[0].get("languageCode", "")
            break

    texts = []
    for block in blocks:
        lines = block.get("lines", [])
        for line in lines:
            text_content = line.get("text", "")
            bounding_box = line.get("boundingBox", {})
            vertices = bounding_box.get("vertices", [])
            if text_content and len(vertices) >= 4:
                x_min, y_min = int(vertices[0].get("x", 0)), int(vertices[0].get("y", 0))
                x_max, y_max = int(vertices[2].get("x", 0)), int(vertices[2].get("y", 0))
                ocr_text = OCRText(
                    text=text_content,
                    bbox=BBox.of_xyxy(x_min, y_min, x_max, y_max).int(),
                )
                texts.append(ocr_text)

    return OCROutput(lang=lang, texts=texts)


@serve.deployment(ray_actor_options={})
class OCRReaderYandex:
    def __init__(self):
        dotenv.load_dotenv()
        ya_folder = os.getenv("YC_FOLDER_ID")
        ya_api_token = os.getenv("YC_API_KEY")
        self._session = aiohttp.ClientSession(
            base_url="https://ocr.api.cloud.yandex.net/ocr/",
            headers={
                "Authorization": f"Api-Key {ya_api_token}",
                "x-folder-id": ya_folder,
                "x-data-logging-enabled": "true"
            }
        )

    async def __call__(self, image, prefer_lang="*") -> Optional[OCROutput]:
        image = cv2_to_b64png(image)

        async with self._session.post(
                "v1/recognizeText",
                json={
                    "mimeType": "JPEG",
                    "languageCodes": [prefer_lang],
                    "model": "page",
                    "content": image
                }
        ) as response:
            if response.status != 200:
                return None
            data = await response.json()
            data = decode_response(data)
            return data


if __name__ == "__main__":
    app = serve.run(OCRReaderYandex.bind())
