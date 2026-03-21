from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions, PdfPipelineOptions
from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from pydantic import AnyUrl

from src.utils.aimodel import load_llm_conf


def _docling_olm():
    prompt = (
        "Attached is one page of a document that you must process. "
        "Convert it to HTML representation of this document as if you were reading it naturally using a browser. Convert tables to HTML. Format everything in HTML.\n Add texts, headings, labels, lists and other important page components."
        "If there are any figures, images, charts, diagrams, instead of them print out paragraph with textual description of contents.\n"
    )
    model = load_llm_conf("olmocr")
    pipeline_options = ApiVlmOptions(
        url=AnyUrl(model.url + "/chat/completions"),
        params=dict(
            model=model.model,
            max_tokens=16000,
        ),
        headers={"Authorization": f"Bearer {model.token}"},
        prompt=prompt,
        timeout=60,
        scale=2.0,
        temperature=0.0,
        concurrency=4,
        response_format=ResponseFormat.HTML,
    )
    vlm_pipeline_options = VlmPipelineOptions(
        vlm_options=pipeline_options,
        enable_remote_services=True,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=vlm_pipeline_options,
            ),
        }
    )


def _docling_noocr():
    pipeline_options = PdfPipelineOptions(
        do_ocr=False,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )


def _docling_default():
    return DocumentConverter()


def docling_provider(use_vlm: bool = False, use_ocr: bool = True) -> DocumentConverter:
    if not use_ocr: return _docling_noocr()
    if use_vlm: return _docling_olm()
    return _docling_default()
