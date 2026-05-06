from typing import Tuple, List, Optional, Iterator

from docling_core.transforms.chunker import HybridChunker, DocChunk
from docling_core.types import DoclingDocument
from docling_core.types.doc import PictureItem, TableItem
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt
from docproc.tableproc import doc_table_export


class DocumentSummary(BaseModel):
    title: str
    topic: str
    tags: str
    context: str


class DocumentChunk(BaseModel):
    text: str
    loc_page: Optional[int] = None
    loc_drefs: Optional[List[str]] = None


llm = load_llm_lc("gemini2").with_structured_output(DocumentSummary)


def docling_text_only(ddoc: DoclingDocument) -> Tuple[DocumentSummary, DoclingDocument]:
    res: DocumentSummary = llm.invoke([
        SystemMessage(sprompt("doc", "summary")),
        HumanMessage(ddoc.export_to_markdown())
    ])

    to_remove = []
    for v, _ in ddoc.iterate_items(with_groups=True, traverse_pictures=True):
        if isinstance(v, PictureItem):
            for i_in in v.children:
                to_remove.append(i_in)
            to_remove.append(v)
        if isinstance(v, TableItem):
            td = doc_table_export(ddoc, v)
            if len(td) * len(td[0]) > 50:
                to_remove.append(v)

    doc_clean = ddoc.model_copy(deep=True)
    doc_clean.delete_items(node_items=to_remove)

    return res, doc_clean


def docling_chunk(text_only: DoclingDocument) -> List[DocumentChunk]:
    chunker = HybridChunker()
    chunk_iter: Iterator[DocChunk] = chunker.chunk(dl_doc=text_only)
    res = []
    for chk in chunk_iter:
        dc = DocumentChunk(text=chunker.contextualize(chunk=chk))
        if items := chk.meta.doc_items:
            provs = [i.prov[0] for i in items if i.prov]
            if provs:
                dc.loc_page = provs[0].page_no
            else:
                dc.loc_page = 0
            dc.loc_drefs = [i.self_ref for i in items]
        res.append(dc)
    return res
