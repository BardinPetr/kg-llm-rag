import asyncio
from typing import *

import numpy as np
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt, uprompt
from validate.ragdataset import KGRAGDatasetQuestion, KGRAGDatasetBlock

judge = load_llm_lc("gemini3")


class UnanswerableValidation(BaseModel):
    """
    Check how RAG worked on questions, which could not be answered with given data.
    """
    fail_stated: bool = Field(description="If system explicitly stated what was not found")
    hallucinated: bool = Field(description="Did system hallucinate to try to answer question")
    provided_all_possible: bool = Field(description="System provided extensive existing information including inconsistencies")
    is_helping: bool = Field(description="Did system provide user existing information")
    reasoning: str = Field(description="Why that decision was taken")

check_llm = judge.with_structured_output(UnanswerableValidation)


async def evaluate_tricky(questions: List[KGRAGDatasetQuestion], answers: List[str]) -> Tuple[float, float]:
    results = await asyncio.gather(*[
        check_llm.ainvoke([
            SystemMessage(sprompt(
                "val", "tricky",
                question=q.question,
                golden=q.answer,
                answer=ans,
            ))
        ])
        for q, ans in zip(questions, answers)
        if q.is_trick
    ])
    results = [sum((i.fail_stated, i.provided_all_possible * 0.5, i.is_helping * 0.5)) / 2
               for i in results if not i.hallucinated]
    return (float(np.mean(results)), float(np.std(results))) if len(results) else (1, 0)
