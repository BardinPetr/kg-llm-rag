from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import networkx as nx
from docling_core.types import DoclingDocument
from docling_core.types.io import DocumentStream
from tqdm import tqdm

from db.neo_base import n_setup
from db.neo_doc import *
from db.neo_kg import KType, KFactType
from docproc.improc import docling_extract_images, describe_image, ImageCategory
from docproc.tableproc import extract_tables
from docproc.textproc import docling_text_only, docling_chunk
from document.docling.provider import docling_provider, create_document_processor
from kg.kgextract import doc_extract_kg
from kg.kgingest import entity_dedup_ingest, fact_ingest


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
        metadata=file.metadata,
        stages=[DocumentProcStages.FILE]
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

    try:
        d_content = DocumentStream(name=doc.name, stream=BytesIO(doc.source_file.get().content))
        d_doc = ddp(d_content)
    except:
        doc.delete()
        return None

    doc.refresh()
    doc.stages.append(DocumentProcStages.DOCL)
    doc.docling_file.connect(DObject.make(d_doc))
    doc.save()
    return d_doc


def load_tables(doc: DDocument):
    if DocumentProcStages.TABL in doc.stages: return

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
            stages=[BlockProcStages.LOAD],
            repr=t_descr.context
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

    doc.refresh()
    doc.stages.append(DocumentProcStages.TABL)
    doc.save()


def load_textual(doc: DDocument):
    if DocumentProcStages.TEXT in doc.stages: return

    logger.info(f"{doc.name}: Document text base analysis")
    ddoc: DoclingDocument = load_docling(doc)
    doc.refresh()

    summary, ddoc_text = docling_text_only(ddoc)
    ddoc_md = ddoc_text.export_to_markdown()

    t_block = DTxtBlock(
        title=summary.title,
        own_context=ddoc_md,
        metadata=dict(context=summary.context, topic=summary.topic, tags=summary.tags),
        stages=[BlockProcStages.LOAD],
        repr=summary.context,
    )
    t_block.save()
    t_block.content.connect(DObject.make(ddoc_md))
    t_block.document.connect(doc)

    for chk in docling_chunk(ddoc_text):
        t_chunk = DChunk(repr=chk.text)
        t_chunk.save()
        loc = dict(
            loc_page=chk.loc_page,
            loc_drefs=chk.loc_drefs,
            loc_type="page"
        )
        t_chunk.text_block.connect(t_block, properties=loc)

    doc.refresh()
    doc.repr = summary.context
    doc.stages.append(DocumentProcStages.TEXT)
    doc.save()


def load_visual(doc: DDocument):
    if DocumentProcStages.IMAG in doc.stages: return

    logger.info(f"{doc.name}: Document image analysis")
    ddoc: DoclingDocument = load_docling(doc)

    im_data = docling_extract_images(ddoc)
    im_descr = [describe_image(i.data) for i in im_data]

    logger.info(f"{doc.name}: detected {len(im_data)} image nodes")

    for dat, dsc in zip(im_data, im_descr):
        if not dsc: continue
        if dsc.category == ImageCategory.DROP: continue
        t_block = DImgBlock(
            title=dsc.title,
            own_context=dsc.content,
            metadata=dict(
                preview=dsc.preview,
                type=dsc.category
            ),
            stages=[BlockProcStages.LOAD],
            repr=dsc.preview,
        )
        t_block.save()
        t_block.content.connect(DObject.make(dat))

        loc = dict(
            loc_page=dat.loc_page,
            loc_bind=dat.loc_bind,
            loc_type="page"
        )
        t_block.document.connect(doc, loc)

    doc.refresh()
    doc.stages.append(DocumentProcStages.IMAG)
    doc.save()


def make_block_kg(blk: DBlock) -> nx.DiGraph:
    if kg := blk.kgg.get_or_none(): return kg

    logger.info(f"KG ex: block {type(blk).__name__} '{blk.title[:25]}...'")

    if isinstance(blk, DTxtBlock) or isinstance(blk, DImgBlock):
        doc_input = str(blk.own_context)
    elif isinstance(blk, DTblBlock):
        t_ddoc: DoclingDocument = blk.content.get().content
        doc_input = t_ddoc.export_to_markdown()
    # elif isinstance(blk, DExcelBlock):
    #     pass
    else:
        raise Exception("unknown block type")

    external_context = blk.document.get().repr

    ex_ecls = [i.uid for i in KType.select()]
    ex_fcls = [i.uid for i in KFactType.select()]

    kg = doc_extract_kg(doc_input, external_context, ex_ecls, ex_fcls)

    blk.refresh()
    blk.stages.append(BlockProcStages.NXKG)
    blk.kgg.connect(DObject.make(kg))
    blk.save()

    logger.info(f"KG ex done: block {blk.title[:25]}...")
    return kg


def ingest_entities_blocking(blk: DBlock):
    if BlockProcStages.KGIE in blk.stages: return
    entity_dedup_ingest(blk)
    blk.refresh()
    blk.stages.append(BlockProcStages.KGIE)
    blk.save()


def ingest_facts(blk: DBlock):
    if BlockProcStages.KGIR in blk.stages: return
    fact_ingest(blk)
    blk.refresh()
    blk.stages.append(BlockProcStages.KGIR)
    blk.save()


def embed_all_blocking():
    # to embed: DDocument, DBlock, DChunk, KFact;  skipped: KEntity
    emb_srv = EmbeddingService()
    to_embed = [i for i in DEmbeddable.select(repr_embedding__isnull=True) if i.repr]
    logger.info(f"Embedding {len(to_embed)} documents")
    embeddings = emb_srv.embed_all([i.repr for i in to_embed])
    for n, emb in zip(to_embed, embeddings):
        n.refresh()
        n.repr_embedding = emb
        n.save()
    logger.info("Embedding done")


def ingest_docs(doc_paths: List[Path], clean=False):
    if clean:
        n_setup()
        # n_cls(all=True)

    logger.info("Starting ingest documents")
    docs = []
    for i in doc_paths:
        d = DocumentFile(
            name=i.name,
            content=i.read_bytes()
        )
        k = load_document(d)
        docs.append(k)
    logger.info("Documents created")

    logger.info("Starting docling processing")
    docs2 = []
    for i in docs:
        d = load_docling(i)
        if d: docs2.append(i)
    logger.info("Docling processing done")

    logger.info("Starting loading blocks")
    for i in docs2:
        load_textual(i)
        load_tables(i)
        load_visual(i)
    logger.info("Loading blocks done")

    logger.info("Starting KG extraction")
    for i in tqdm(list(DBlock.iter())):
        make_block_kg(i)
    logger.info("KG extraction done")

    logger.info("Starting KG entity ingestion")
    for i in tqdm(list(DBlock.iter())):
        ingest_entities_blocking(i)
    logger.info("KG entity ingestion done")

    logger.info("Starting KG fact ingestion")
    for i in tqdm(list(DBlock.iter())):
        ingest_facts(i)
    logger.info("KG fact ingestion done")

    embed_all_blocking()

# ingest_docs([Path("/home/petr/study/diploma/workspace/pdf/demo/complex-1.pdf")], clean=False)