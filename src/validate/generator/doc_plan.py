import asyncio
from pathlib import Path
from typing import *

from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from utils.aimodel import load_llm_lc
from utils.file import wr
from utils.prompt import sprompt
from validate.generator.kg import KGGen

llm = load_llm_lc("gemini3pro")


class CorpusGenerationConfig(BaseModel):
    language: str = "Russian"
    num_standard_documents: int = 10
    alias_use_probability: float = 0.9

    noise_level: float = 80
    min_docs_per_chain: int = 3
    entity_reuse_probability: float = 0.9

    num_contradicted_facts: int = 10


allowed_alias_types = [
    "abbreviation",
    "short_form",
    "formal_variant",
    "ocr_noise",
    "transliteration",
    "legal_form_variant",
]
contradiction_types = [
    "value_change",
    "entity_swap",
    "negation"
]

class EntityPlacement(BaseModel):
    entity_uid: str = Field(description="UID of the entity from the KG")
    name_variant: str = Field(description="Exact name string to use in this document — may be canonical or an alias")
    alias_type: Optional[str] = Field(None,
                                      description="Alias transformation applied: abbreviation | short_form | formal_variant | ocr_noise | transliteration | legal_form_variant — null if canonical name is used")


class FactPlacement(BaseModel):
    fact_uid: str = Field(description="UID of the fact from KG values or relations")
    modality: Literal["text", "table", "image"] = Field(
        description="How this fact is presented: text=narrative paragraph, table=HTML table cell, image=embedded figure")
    section_hint: str = Field(
        description="Document section where this fact should appear, e.g. 'Shareholders Section', 'Directors Table'")


class ImageSpec(BaseModel):
    image_id: str = Field(description="Unique image identifier used as filename: img_001, img_002, etc.")
    image_type: str = Field(description="Visual type: org_chart | id_card | stamp | bar_chart | signature_block | map")
    vlm_generation_prompt: str = Field(
        description="Complete self-contained prompt for image generation model. Must name entities using their document-specific name_variant and visually encode the assigned fact.")


class ContradictionSpec(BaseModel):
    original_fact_uid: str = Field(description="UID of the fact being contradicted from the main corpus")
    contradiction_type: str = Field(
        description="value_change: different number/date | entity_swap: different entity | negation: opposite state")
    contradicted_value: str = Field(description="The incorrect value this document asserts instead of the true value")


class DocumentPlan(BaseModel):
    uid: str = Field(description="Unique document identifier: doc_001, doc_002, etc.")
    filename: str = Field(description="HTML filename: shareholder_register_2023.html")
    title: str = Field(description="Document title as shown in the document header")
    language: str = Field(description="Language for document text generation")
    description: str = Field(description="What type of document this is, who issued it, its purpose in the corpus")
    generation_instructions: str = Field(
        description="Specific additional instructions for the document generation step")
    entity_usages: List[EntityPlacement] = Field(
        description="All entities appearing in this document with their exact name variants")
    fact_placements: List[FactPlacement] = Field(
        description="All KG facts that must appear in this document with their assigned modality")
    image_specs: List[ImageSpec] = Field(
        description="One entry per image-modality fact, providing the VLM generation prompt")
    noise_topics: List[str] = Field(
        description="Realistic off-KG topics to pad the document with, e.g. 'standard legal disclaimer', 'company address block'")
    is_inconsistency_doc: bool = Field(False,
                                       description="True if this document deliberately contradicts facts from other documents")
    contradictions: List[ContradictionSpec] = Field(default_factory=list,
                                                    description="Facts contradicted by this document — only populated when is_inconsistency_doc=True")


class CorpusPlan(BaseModel):
    documents: List[DocumentPlan] = Field(description="All planned documents including optional inconsistency document")
    distribution_rationale: str = Field(
        description="Explanation of how facts were split across documents and why no single document answers the key questions alone")
    multi_hop_guarantee: str = Field(
        description="Concrete examples: 'To find UBO of Entity X a system must read doc_001 (ownership %) then doc_003 (controller identity)'")


class GeneratedDocument(BaseModel):
    document_uid: str = Field(description="Matches uid from DocumentPlan")
    html: str = Field(description="Complete well-formed HTML document. No markdown, no code fences.")


def kg_ser(kg):
    return kg.model_dump_json(indent=2)


def plan_corpus(kg: KGGen) -> CorpusPlan:
    ppt = SystemMessage(sprompt(
        "dsgen", "plan",
        kg_json=kg_ser(kg),
        language="russian",
        num_standard_documents=10,
        text_pct=50,
        table_pct=40,
        image_pct=10,
        entity_reuse_prob=40,
        alias_prob=80,
        alias_types=allowed_alias_types,
        min_docs_per_chain=3,
        noise_level=80,
        num_contradicted_facts=10,
        include_inconsistency=True,
        contradiction_types=contradiction_types,
    ))
    return llm.with_structured_output(CorpusPlan).invoke([ppt])


def g_ppt(kg, spec):
    return sprompt(
        "dsgen", "make",
        plan_json=spec.model_dump_json(indent=2),
        language="russian",
        kg_json=kg_ser(kg),
        noise_pct=70,
    )


gen = llm.with_structured_output(GeneratedDocument)


async def generate_corpus(kg: KGGen, spec: CorpusPlan, out_dir):
    documents = await asyncio.gather(*[
        gen.ainvoke([SystemMessage(g_ppt(kg, spec))])
        for spec in spec.documents
    ])

    dataset = Path(out_dir)
    for i in dataset.iterdir():
        i.unlink()

    for spec, doc in zip(spec.documents, documents):
        wr(dataset / spec.filename, doc.html)

    return documents
