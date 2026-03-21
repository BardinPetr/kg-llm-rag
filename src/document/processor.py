import asyncio
from pathlib import Path
from typing import Optional

from docling_core.types import DoclingDocument
from ray import serve
from ray.serve.handle import DeploymentHandle

from src.document.docling.docling_processor import PDFProcessorDocling, PDFProcessorDoclingVLM
from document.model.model import DocumentResult
from document.pdf.odl_processor import PDFProcessorODL
from src.document.table.table import DocumentTableProcessor
from document.util.textcheck import check_text_adequate
from src.visual.analyze.structure.linegraph import uid


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class DocumentProcessor:
    def __init__(self,
                 docling: DeploymentHandle[PDFProcessorDocling],
                 docling_vlm: DeploymentHandle[PDFProcessorDoclingVLM],
                 odl: DeploymentHandle[PDFProcessorODL],
                 table: DeploymentHandle[DocumentTableProcessor]):
        self._docling = docling
        self._docling_vlm = docling_vlm
        self._odl = odl
        self._table = table

    async def __call__(self, file: Path) -> DocumentResult:
        print(f"Start loading {file}")

        res = await asyncio.gather(
            self._docling.remote(file),
            self._odl.remote(file),
        )
        docling_res: Optional[DoclingDocument] = res[0]
        odl_html: Optional[str] = res[1]

        vlm_needed = docling_res is None or not check_text_adequate(docling_res.export_to_text())
        if vlm_needed:
            print(f"VLM requested for {file}")
            docling_res = await self._docling_vlm.remote(file)
            print(f"VLM done for {file}")

        print(f"Table analysis for {file}")
        table_data = await self._table.remote([docling_res.export_to_html()] + ([odl_html] if odl_html else []))

        print(f"End loading {file}")
        return DocumentResult(
            id=uid(),
            file=str(file),
            doc=docling_res,
            tables=table_data
        )
