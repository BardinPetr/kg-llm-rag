from typing import *

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt, uprompt
from validate.ragdataset import KGRAGDatasetQuestion, KGRAGDatasetBlock

judge = load_llm_lc("gemini3")


class ClaimExtractionResult(BaseModel):
    """Atomic claims extracted from the RAG answer."""
    claims: List[str] = Field(description="List of atomic, self-contained factual statements")


claim_llm = judge.with_structured_output(ClaimExtractionResult)


async def extract_claims(question, answer) -> List[str]:
    res: ClaimExtractionResult = await claim_llm.ainvoke([
        SystemMessage(sprompt(
            "val", "factclaim",
            question=question,
            answer=answer,
        ))
    ])
    return res.claims


class ClaimCheck(BaseModel):
    claim: str
    relevant: bool
    confirmable: bool
    reason: str


class ClaimPrecisionResult(BaseModel):
    claims: List[ClaimCheck]


precision_llm = judge.with_structured_output(ClaimPrecisionResult)


async def evaluate_precision(current_block: KGRAGDatasetBlock, q_def: KGRAGDatasetQuestion, result: str) -> Dict:
    if q_def.is_unanswerable: raise ValueError("not for trick questions")
    claims = await extract_claims(q_def.question, result)
    res: List[ClaimCheck] = (await precision_llm.ainvoke([
        SystemMessage(sprompt("val", "factprecision")),
        HumanMessage(uprompt(
            "val", "factprecision",
            question=q_def.question,
            golden_answer=result,
            claims=claims,
            documents=current_block.document_contexts
        ))
    ])).claims

    total = len(res)
    valid_relevant = sum(1 for c in res if c.relevant and c.confirmable)
    valid = sum(1 for c in res if c.confirmable)
    hallucinated = sum(1 for c in res if not c.confirmable)
    return dict(
        precision=valid_relevant / total if total else 1,
        hallucination=hallucinated / total if total else 0
    )
