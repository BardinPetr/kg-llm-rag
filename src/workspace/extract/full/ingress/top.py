from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import *

from docling_core.transforms.chunker import HybridChunker
from docling_core.types import DoclingDocument
from docling_core.types.io import DocumentStream
from loguru import logger

from document.docling.provider import docling_provider, create_document_processor
from utils.file import do_hash
from workspace.extract.full.doclingtext import docling_text_only, docling_chunk
from workspace.extract.full.doclingvisual import docling_extract_images, describe_image
from workspace.extract.full.neomd import DObject, DDocument, DTblBlock, n_cls, DTxtBlock, DChunk, \
    DImgBlock
from workspace.extract.full.tableextract import extract_tables


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


def load_document(file: DocumentFile):
    doc_file = DObject.make(file.content)
    if doc_file.refs:
        logger.warning(f"File {file.name} exist by content")
        return doc_file.refs[0]

    doc = DDocument(
        name=file.name,
        metadata=file.metadata
    )
    doc.save()
    doc.source_file.connect(doc_file)
    return doc


ddp = docling_provider(use_vlm=False)
ddp = create_document_processor(ddp, "./ccache")


def load_docling(doc: DDocument) -> DoclingDocument:
    doc.refresh()
    if doc.docling_file:
        logger.info(f"Docling present for {doc.name}")
        return doc.docling_file.get_or_none().content

    d_content = DocumentStream(name=doc.name, stream=BytesIO(doc.source_file.get().content))
    d_doc = ddp(d_content)

    doc.refresh()
    doc.docling_file.connect(DObject.make(d_doc))
    doc.save()
    return d_doc


def load_tables(doc: DDocument):
    logger.info(f"Extracting tables from {doc.name}")
    ddoc: DoclingDocument = load_docling(doc)
    tables = extract_tables(ddoc)

    logger.info(f"{doc.name}: detected {len(tables)} table nodes")
    for t_descr, t_prov, t_data in tables:
        t_block = DTblBlock(
            title=t_descr.title,
            own_context=t_descr.context,
            metadata=dict(
                transpose=not t_descr.header_top,
                processing=t_descr.altered
            ),
            # repr,
            # repr_embedding # TODO
        )
        t_block.save()
        t_block.content.connect(DObject.make(t_data))

        loc = dict(
            loc_page=t_prov.loc_page,
            loc_bind=t_prov.loc_title,
            loc_drefs=t_prov.loc_drefs,
            loc_didx=t_prov.loc_didx,
            loc_type="page"
        )
        t_block.document.connect(doc, loc)


def load_textual(doc: DDocument):
    logger.info(f"{doc.name}: Document text base analysis")
    ddoc: DoclingDocument = load_docling(doc)

    summary, ddoc_text = docling_text_only(ddoc)
    ddoc_md = ddoc_text.export_to_markdown()

    t_block = DTxtBlock(
        title=summary.title,
        own_context=summary.context,
        metadata=dict(topic=summary.topic, tags=summary.tags),
        # repr,  from summary.context
        # repr_embedding # TODO
    )
    t_block.save()
    t_block.content.connect(DObject.make(ddoc_md))
    t_block.document.connect(doc)

    for chk in docling_chunk(ddoc_text):
        t_chunk = DChunk(
            repr=chk.text,
            # repr_embedding # TODO
        )
        t_chunk.save()
        loc = dict(
            loc_page=chk.loc_page,
            loc_drefs=chk.loc_drefs,
            loc_type="page"
        )
        t_chunk.text_block.connect(t_block, properties=loc)


def load_visual(doc: DDocument):
    logger.info(f"{doc.name}: Document image analysis")
    ddoc: DoclingDocument = load_docling(doc)

    im_data = docling_extract_images(ddoc)
    im_descr = [describe_image(i.data) for i in im_data]

    logger.info(f"{doc.name}: detected {len(im_data)} table nodes")

    for dat, dsc in zip(im_data, im_descr):
        t_block = DImgBlock(
            title=dsc.title,
            own_context=dsc.content,
            metadata=dict(
                preview=dsc.preview,
                type=dsc.category
            ),
            # repr,
            # repr_embedding # TODO
        )
        t_block.save()
        t_block.content.connect(DObject.make(dat))

        loc = dict(
            loc_page=dat.loc_page,
            loc_bind=dat.loc_bind,
            loc_type="page"
        )
        t_block.document.connect(doc, loc)

if __name__ == "__main__":
    # n_setup()
    n_cls(all=True)

    docs = []
    dirr = Path("/home/petr/study/diploma/src/workspace/extract/demo")
    for i in dirr.iterdir():
        d = DocumentFile(
            name=i.name,
            content=i.read_bytes()
        )
        k = load_document(d)
        docs.append(k)

    for i in docs:
        d = load_docling(i)

    for i in docs:
        load_tables(i)
        load_textual(i)
        load_visual(i)
