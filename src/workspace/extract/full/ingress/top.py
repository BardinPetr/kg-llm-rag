from dataclasses import dataclass, field
from pathlib import Path
from typing import *

from neomodel import UniqueProperty

from utils.file import do_hash
from workspace.extract.full.neomd import KDocument, DObject
from loguru import logger


@dataclass
class DocumentFile:
    name: str
    content: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def of_file(cls, path: Path) -> 'DocumentFile':
        return DocumentFile(
            name=path.name,
            content=path.read_bytes()
        )

    def hash(self) -> str:
        return do_hash(self.content)


# def ingress_txt_doc():
#     pass
#
# def ingress_img_doc():
#     pass
#
# def ingress_tbl_doc():
#     pass
#
# def ingress_doc_by_type():
#     match x:
#         case _:
#             return ingress_txt_doc()
#         case _:
#             return ingress_tbl_doc()
#         case _:
#             return ingress_img_doc()


def docling_load(doc_):
    return ...


def load_document(file: DocumentFile):
    doc_file = DObject()
    doc_file.content = file.content
    try:
        doc_file.save()
    except UniqueProperty:
        logger.warning(f"File {file.name} exist by content")
        return False

    doc = KDocument(
        name=file.name,
        metadata=file.metadata
        # TODO
    )
    doc.save()
    doc.original_file.connect(doc_file)

def load_docling():



dirr = Path("/home/petr/study/diploma/src/workspace/extract/demo")
for i in dirr.iterdir():
    d = DocumentFile(
        name=i.name,
        content=i.read_bytes()
    )
    load_document(d)
