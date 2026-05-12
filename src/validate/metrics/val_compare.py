import asyncio
from collections import defaultdict
from typing import List

import pandas as pd
from langchain_core.messages import SystemMessage
from pydantic import BaseModel

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt
from validate.ragdataset import KGRAGDatasetQuestion

judge = load_llm_lc("gemini3")


class CompareResult(BaseModel):
    """
    Compare and rank answers by criterion.
    Provide ranks as list of answer numbers, order from best to worst, answer numbering from 1.
    For example, if answer 1 is better than answer 2, then array would be [1, 2].
    """
    comprehensiveness: List[int]
    empowerment: List[int]
    directness: List[int]
    diversity: List[int]
    reasoning: str


compare_llm = judge.with_structured_output(CompareResult)


async def evaluate_one(question: str, answers: List[str]) -> List[List[int]]:
    res: CompareResult = await compare_llm.ainvoke([
        SystemMessage(sprompt(
            "val", "compare",
            question=question,
            answers='\n----\n'.join([f"\n--ANSWER#{i}--\n{v}" for i, v in enumerate(answers)])
        ))
    ])
    try:
        ranks = [[] for _ in range(len(answers))]
        for crit in (res.comprehensiveness, res.empowerment, res.directness, res.diversity):
            for rank, name in enumerate(crit):
                ranks[int(name) - 1].append(rank + 1)
    except IndexError:
        return None
    return ranks


async def evaluate_comparing_out_mrr(questions: List[KGRAGDatasetQuestion], answers: List[List[str]]) -> List[float]:
    cnt = len(answers)
    answers = list(zip(*answers))
    results = await asyncio.gather(*[
        evaluate_one(q.question, ass) for q, ass in zip(questions, answers)
    ])
    d = pd.DataFrame.from_dict(results)
    return (1 / d.explode(list(range(cnt)))).mean().to_list()
