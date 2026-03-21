from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.exceptions import ConversionError
from docling_core.types import DoclingDocument
from ray import serve

from src.document.docling.provider import docling_provider


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class PDFProcessorDocling:
    def __init__(self):
        self._dumb_converter = docling_provider(use_vlm=False, use_ocr=False)
        self._converter = docling_provider(use_vlm=False, use_ocr=True)

    def load_html(self, html_text: str) -> Optional[DoclingDocument]:
        try:
            res = self._dumb_converter.convert_string(html_text, format=InputFormat.HTML)
        except ConversionError:
            print("Failed converting HTML text to docling")
            return None
        return res.document if res.status == ConversionStatus.SUCCESS else None

    def __call__(self, file: Path) -> Optional[DoclingDocument]:
        res = self._converter.convert(file, raises_on_error=False)
        return res.document if res.status == ConversionStatus.SUCCESS else None


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class PDFProcessorDoclingVLM:
    def __init__(self):
        self._converter = docling_provider(use_vlm=True)

    def __call__(self, file: Path) -> Optional[DoclingDocument]:
        res = self._converter.convert(file, raises_on_error=False)
        return res.document if res.status == ConversionStatus.SUCCESS else None
