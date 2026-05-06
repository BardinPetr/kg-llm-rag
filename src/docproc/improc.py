import base64
from enum import StrEnum
from io import BytesIO
from typing import List, Optional

from docling_core.types import DoclingDocument
from docling_core.types.doc import PictureItem, SectionHeaderItem
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from document.docling.provider import docling_provider, create_document_processor
from utils.aimodel import load_llm_lc
from utils.prompt import sprompt


class ImageCategory(StrEnum):
    CHART = "CHART"
    DIAGRAM = "DIAGRAM"
    INFOGRAPHIC = "INFOGRAPHIC"
    SCREENSHOT = "SCREENSHOT"
    MATH = "MATH"
    PHOTO = "PHOTO"
    MIX = "MIX"
    DROP = "DROP"


class ImageAnalysisResult(BaseModel):
    category: ImageCategory
    title: str
    preview: str
    content: str


class DocumentImage(BaseModel):
    loc_page: Optional[int]
    loc_bind: Optional[str]
    loc_drefs: Optional[List[str]]
    loc_didx: Optional[int]
    data: bytes


ddp = docling_provider(use_vlm=False)
ddp = create_document_processor(ddp, "./ccache")
vllm = load_llm_lc("gemini2").with_structured_output(ImageAnalysisResult)


def load_img(im: PictureItem) -> bytes:
    if im.image is None: return b''
    buffered = BytesIO()
    im.image.pil_image.save(buffered, format="PNG")
    return buffered.getvalue()


def docling_extract_images(ddoc: DoclingDocument) -> List[DocumentImage]:
    to_drop = []
    img_elements: List[DocumentImage] = []
    last_header = None
    for ii, (v, _) in enumerate(ddoc.iterate_items(with_groups=True, traverse_pictures=True)):
        if isinstance(v, SectionHeaderItem):
            last_header = v.text
        if isinstance(v, PictureItem):
            loc = v.prov[0].bbox
            for i_in in v.children:
                to_drop.append(i_in)
            if loc.area() < 50 * 50:
                to_drop.append(v)
            else:
                data = load_img(v)
                img_elements.append(DocumentImage(
                    loc_page=v.prov[0].page_no,
                    loc_bind=last_header,
                    loc_drefs=[v.self_ref],
                    loc_didx=ii,
                    data=data
                ))
            last_header = None

    im_doc = ddoc.model_copy(deep=True)
    im_doc.delete_items(node_items=to_drop)
    return img_elements


def describe_image(data: bytes) -> Optional[ImageAnalysisResult]:
    if not data: return None
    img_base64 = base64.b64encode(data).decode()
    return vllm.invoke([
        SystemMessage(sprompt("img", "describe")),
        HumanMessage(content=[{
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        }])
    ])
