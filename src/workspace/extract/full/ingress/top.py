from dataclasses import dataclass, field
from pathlib import Path
from typing import *

from utils.file import do_hash
from workspace.extract.full.datastore.objstore import store_object
from workspace.extract.full.neomd import KDocument


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


def load_document(doc: DocumentFile):
    doc_ref = doc.hash()

    store_object(doc_ref, doc.content)
    doc = KDocument(
        ref=doc_ref,
        name=doc.name,
        metadata=doc.metadata
        # TODO
    ).save()
    doc_id = doc.id

    # docling_doc = docling_load(doc.content)

    # doc = insert_document(doc_obj_ref)
    # ingress_doc_by_type()
