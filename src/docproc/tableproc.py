from enum import StrEnum
from typing import List, Tuple, Optional

from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.datamodel.document import ConversionResult
from docling_core.types import DoclingDocument
from docling_core.types.doc import TableItem, DocItemLabel
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from document.docling.provider import docling_provider
from utils.aimodel import load_llm_lc
from utils.prompt import sprompt


class TableAlteringReason(StrEnum):
    HEADER = "HEADER"
    COLUMNS = "COLUMNS"
    SPLIT = "SPLIT"


class LLMTableExtractBlock(BaseModel):
    doc_part_identifier: int
    original_table_title: str
    title: str
    context: str
    table_html: str
    header_top: bool
    altered: List[TableAlteringReason]


class TableProv(BaseModel):
    loc_page: Optional[int]
    loc_title: Optional[str]
    loc_drefs: Optional[List[str]]
    loc_didx: Optional[int]


class LLMTableExtractResult(BaseModel):
    tables: List[LLMTableExtractBlock]


dumb_docling = docling_provider(use_vlm=False, use_ocr=False)
llm = load_llm_lc("gemini2").with_structured_output(LLMTableExtractResult)


def html2docling(x) -> ConversionResult:
    return dumb_docling.convert_string(x, format=InputFormat.HTML)


def doc_table_export(doc, tbl) -> List[List[str]]:
    if tbl.data.num_rows == 0 or tbl.data.num_cols == 0:
        return []
    return [[cell._get_text(doc=doc) for cell in row] for row in tbl.data.grid]


def extract_tables(ddoc: DoclingDocument) -> List[Tuple[LLMTableExtractBlock, TableProv, DoclingDocument]]:
    t_doc = ddoc.model_copy(deep=True)

    table_map = {}
    for ii, (v, _) in enumerate(ddoc.iterate_items(with_groups=True, traverse_pictures=True)):
        if isinstance(v, TableItem):
            table_map[ii] = v
            t_doc.insert_text(v, DocItemLabel.TEXT, text=f"'doc_part_identifier={ii}'")

    res: LLMTableExtractResult = llm.invoke([
        SystemMessage(sprompt("doc", "table")),
        HumanMessage(t_doc.export_to_html())
    ])

    result = []
    for t_res in res.tables:
        if (tbl := table_map.get(int(t_res.doc_part_identifier), None)) is None: continue

        prov = TableProv(
            loc_page=tbl.prov[0].page_no if tbl.prov else 0,
            loc_title=t_res.original_table_title,
            loc_drefs=[tbl.self_ref],
            loc_didx=int(t_res.doc_part_identifier)
        )

        doc_res = html2docling(t_res.table_html)
        if doc_res.status != ConversionStatus.SUCCESS: continue
        cur_doc = doc_res.document

        t_data = doc_table_export(cur_doc, cur_doc.tables[0])
        if len(t_data) * len(t_data[0]) < 50: continue

        result.append((t_res, prov, cur_doc))

    return result
