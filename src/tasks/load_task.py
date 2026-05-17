from celery import group
from more_itertools import flatten

from tasks.clq import clq, redis
from loguru import logger


@clq.task
def embed_task():
    from load.top import embed_all
    logger.info("[embed] acquiring lock")
    with redis.lock('t-embedding'):
        logger.info("[embed] started")
        embed_all()
        logger.info("[embed] done")


@clq.task
def block_fact_task(b_uid):
    from load.top import ingest_facts, DBlock
    logger.info(f"[block_fact] block={b_uid}")
    ingest_facts(DBlock.get(uid=b_uid))
    logger.info(f"[block_fact] done block={b_uid}")


@clq.task
def block_entity_task(b_uid):
    from load.top import ingest_entities, DBlock
    logger.info(f"[block_entity] acquiring lock block={b_uid}")
    with redis.lock('t-entity'):
        logger.info(f"[block_entity] block={b_uid}")
        ingest_entities(DBlock.get(uid=b_uid))
        logger.info(f"[block_entity] done block={b_uid}")


@clq.task
def block_kg_task(b_uid):
    from load.top import make_block_kg, DBlock
    logger.info(f"[block_kg] block={b_uid}")
    b = DBlock.get(uid=b_uid)
    make_block_kg(b)
    logger.info(f"[block_kg] done block={b_uid}")


@clq.task
def extract_txtb_task(d_uid):
    from load.top import load_textual, DDocument
    logger.info(f"[extract_txt] doc={d_uid}")
    if d := DDocument.get(uid=d_uid):
        result = load_textual(d)
        logger.info(f"[extract_txt] done doc={d_uid} blocks={len(result)}")
        return result
    return []


@clq.task
def extract_tblb_task(d_uid):
    from load.top import load_tables, DDocument
    logger.info(f"[extract_tbl] doc={d_uid}")
    if d := DDocument.get(uid=d_uid):
        result = load_tables(d)
        logger.info(f"[extract_tbl] done doc={d_uid} blocks={len(result)}")
        return result
    return []


@clq.task
def extract_imgb_task(d_uid):
    from load.top import load_visual, DDocument
    logger.info(f"[extract_img] doc={d_uid}")
    if d := DDocument.get(uid=d_uid):
        result = load_visual(d)
        logger.info(f"[extract_img] done doc={d_uid} blocks={len(result)}")
        return result
    return []


@clq.task
def load_docling_task(d_uid):
    from load.top import load_docling, DDocument
    if d := DDocument.get(uid=d_uid):
        logger.info(f"[docling] [1/5] doc={d_uid} loading")
        if load_docling(d):
            logger.info(f"[docling] [2/5] doc={d_uid} extracting blocks")
            bgp = group(f.s(d.uid) for f in [extract_txtb_task, extract_tblb_task, extract_imgb_task])().get()
            blks = list(flatten(bgp))

            logger.info(f"[docling] [3/5] doc={d_uid} kg blocks={len(blks)}")
            group(block_kg_task.s(i) for i in blks)().get()

            logger.info(f"[docling] [4/5] doc={d_uid} entities blocks={len(blks)}")
            group(block_entity_task.s(i) for i in blks)().get()

            logger.info(f"[docling] [5/5] doc={d_uid} facts blocks={len(blks)}")
            group(block_fact_task.s(i) for i in blks)().get()

            logger.info(f"[docling] done doc={d_uid} embed queued")
            embed_task.delay()
        else:
            logger.warning(f"[docling] doc={d_uid} failed")


@clq.task
def execute_load_task(doc):
    from load.top import load_document, DocumentProcStages
    logger.info(f"[load] doc={doc.name}")
    res = load_document(doc)
    logger.info(f"[load] done doc={doc.name} uid={res.uid} queuing docling")
    load_docling_task.delay(res.uid).get()
    res.refresh()
    res.stages.append(DocumentProcStages.KGLD)
    res.save()
    return res
