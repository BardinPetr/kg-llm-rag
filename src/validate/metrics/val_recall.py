from typing import *

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt, uprompt
from validate.ragdataset import KGRAGDatasetQuestion


class FactRecallCheck(BaseModel):
    claim: str
    reason: str
    confirmed: bool


class FactRecallResult(BaseModel):
    entity_checks: List[FactRecallCheck]
    fact_extract_checks: List[FactRecallCheck]
    fact_derive_checks: List[FactRecallCheck]


judge = load_llm_lc("gemini3")
recall_llm = judge.with_structured_output(FactRecallResult)


async def evaluate_recall(q_def: KGRAGDatasetQuestion, result: str) -> Dict:
    if q_def.is_unanswerable: raise ValueError("not for trick questions")
    res: FactRecallResult = await recall_llm.ainvoke([
        SystemMessage(sprompt("val", "factrecall")),
        HumanMessage(uprompt(
            "val", "factrecall",
            question=q_def.question,
            answer=result,
            claims=q_def.golden_claims
        ))
    ])

    def _r(x: List[FactRecallCheck]) -> float:
        if len(x) == 0: return 1
        return sum([bool(i.confirmed) for i in x]) / len(x)

    return dict(
        recall_entity=_r(res.entity_checks),
        recall_fact_extract=_r(res.fact_extract_checks),
        recall_fact_derive=_r(res.fact_derive_checks),
        recall=_r(res.entity_checks + res.fact_extract_checks + res.fact_derive_checks)
    )
