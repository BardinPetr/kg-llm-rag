from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from docling_core.types import DoclingDocument
from docling_core.types.doc import NodeItem, PictureItem, TableItem, TextItem
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt


class NodeModality(str, Enum):
    MIX = "MIX"
    TEXT = "TEXT"
    TABLE = "TABLE"
    IMAGE = "IMAGE"


class SemanticChunk(BaseModel):
    """A single flat semantic chunk of the document."""

    caption: str = Field(description="Short descriptive title for this chunk")
    context: str = Field(description="Self-contained context description for this chunk")
    external_context: str = Field(description="Accumulated context from parent / sibling scopes")
    nodes: List[int] = Field(description="Ordered document node IDs belonging to this chunk")
    modality: NodeModality = Field(default=NodeModality.TEXT)
    rendered: Optional[str] = None
    content: List[Any] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class SemanticDocument(BaseModel):
    """Top-level result returned by semantic_chunk()."""

    doc_context: str = Field(description="Global document context")
    chunks: List[SemanticChunk] = Field(description="Flat ordered list of semantic chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class _LLMChunk(BaseModel):
    caption: str = Field(description="Short title for this chunk (≤ 12 words)")
    context: str = Field(
        description=(
            "Self-contained, prompt-ready description of what this chunk is about. "
            "Must be understandable without reading the rest of the document. "
            "Include the document-level theme if relevant."
        )
    )
    nodes: List[int] = Field(description="Ordered list of document node IDs that belong to this chunk")


class _LLMResponse(BaseModel):
    document_context: str = Field(
        description=(
            "One-paragraph global description of the whole document: "
            "its purpose, domain, key entities, and structure."
        )
    )
    chunks: List[_LLMChunk] = Field(
        description="Flat, ordered list of semantic chunks covering every node exactly once."
    )


def _find_consecutive(numbers: List[int]) -> List[Tuple[int, int]]:
    """Convert a list of node IDs into consecutive (start, end) ranges."""
    if not numbers:
        return []
    sorted_nums = sorted(set(numbers))
    segments: List[Tuple[int, int]] = []
    start = end = sorted_nums[0]
    for n in sorted_nums[1:]:
        if n == end + 1:
            end = n
        else:
            segments.append((start, end))
            start = end = n
    segments.append((start, end))
    return segments


def _infer_modality(items: List[NodeItem]) -> NodeModality:
    has_image = any(isinstance(i, PictureItem) for i in items)
    has_table = any(isinstance(i, TableItem) for i in items)
    if has_image and not has_table: return NodeModality.IMAGE
    if has_table and not has_image: return NodeModality.TABLE
    if has_image or has_table:      return NodeModality.MIX
    return NodeModality.TEXT


def linearize_document(doc: DoclingDocument) -> Dict[int, Tuple[NodeItem, int]]:
    """Return {node_id: (NodeItem, indent_level)} for every node in the document."""
    return {
        i: v
        for i, v in enumerate(
            doc.iterate_items(with_groups=True, traverse_pictures=True)
        )
    }


def _serialize_for_llm(
        doc_struct: Dict[int, Tuple[NodeItem, int]],
        max_preview: int = 120,
) -> str:
    """
    Produce a compact, numbered node listing for the LLM prompt.
    Each line: <id> | <label> | <level> | <preview>
    """
    lines: List[str] = []
    for ix, (item, level) in sorted(doc_struct.items()):
        indent = "  " * level

        if isinstance(item, TextItem):
            raw = item.text.replace("\n", " ").strip()
            preview = raw[:max_preview] + ("…" if len(raw) > max_preview else "")
            preview = f'"{preview}"'

        elif isinstance(item, TableItem):
            try:
                header = [c.text for c in item.data.grid[0]]
                first_col = [r[0].text for r in item.data.grid[1:6]]  # up to 5 rows
                preview = f"header={header}; first_col_sample={first_col}"
            except Exception:
                preview = "(table — no preview)"

        elif isinstance(item, PictureItem):
            preview = "(image)"

        else:
            preview = ""

        lines.append(f"{ix:>4} | {indent}{item.label.value:<20} | lvl={level} | {preview}")

    return "\n".join(lines)


def _render_chunk(
        doc: DoclingDocument,
        chunk: _LLMChunk,
        doc_context: str,
) -> str:
    """Render the markdown content for a chunk using docling's own exporter."""
    ranges = _find_consecutive(chunk.nodes)
    parts: List[str] = []
    for fi, ti in ranges:
        md = doc.export_to_markdown(from_element=fi, to_element=ti + 1)
        if md.strip():
            parts.append(md)
    body = "\n\n".join(parts)

    return (
        f"## {chunk.caption}\n\n"
        f"<!-- context: {chunk.context} -->\n\n"
        f"<!-- document context: {doc_context} -->\n\n"
        f"{body}"
    )


def semantic_chunk(doc: DoclingDocument) -> SemanticDocument:
    doc_struct = linearize_document(doc)
    node_listing = _serialize_for_llm(doc_struct)

    llm = load_llm_lc("gemini3").with_structured_output(_LLMResponse)
    llm_response: _LLMResponse = llm.invoke([
        SystemMessage(sprompt("doc", "semchunk")),
        HumanMessage(node_listing)
    ])

    all_doc_ids = set(doc_struct.keys())
    all_chunk_ids: set[int] = set()
    for ch in llm_response.chunks:
        all_chunk_ids.update(ch.nodes)

    missing = all_doc_ids - all_chunk_ids
    unexpected = all_chunk_ids - all_doc_ids
    coverage = 1 - len(missing) / max(len(all_doc_ids), 1)
    print(f"[semantic_chunk] coverage={coverage:.1%}  "
          f"missing={len(missing)}  unexpected={len(unexpected)}")

    doc_context = llm_response.document_context
    chunks: List[SemanticChunk] = []

    accumulated_context = doc_context

    for llm_chunk in llm_response.chunks:
        content_items = [
            doc_struct[nid][0]
            for nid in llm_chunk.nodes
            if nid in doc_struct
        ]

        rendered = _render_chunk(doc, llm_chunk, doc_context)

        chunk = SemanticChunk(
            caption=llm_chunk.caption,
            context=llm_chunk.context,
            external_context=accumulated_context,
            nodes=llm_chunk.nodes,
            modality=_infer_modality(content_items),
            rendered=rendered,
            content=content_items,
        )
        chunks.append(chunk)

        accumulated_context = (
            f"{accumulated_context}\n"
            f"[Chunk: {llm_chunk.caption}] {llm_chunk.context}"
        )

    return SemanticDocument(
        doc_context=doc_context,
        chunks=chunks,
        metadata={
            "total_nodes": len(all_doc_ids),
            "total_chunks": len(chunks),
            "coverage": coverage,
            "missing_nodes": sorted(missing),
            "unexpected_nodes": sorted(unexpected),
        },
    )
