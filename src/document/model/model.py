from dataclasses import dataclass

from docling_core.types import DoclingDocument


@dataclass
class DocumentTables:
    doc: DoclingDocument


@dataclass
class DocumentResult:
    id: str
    file: str
    doc: DoclingDocument
    tables: DocumentTables
