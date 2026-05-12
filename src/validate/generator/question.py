import asyncio
import json
from typing import *

from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from utils.aimodel import load_llm_lc
from validate.generator.doc_plan import CorpusPlan
from validate.generator.kg import KGGen
from validate.generator.q_prompts import fmt_q_ppt


class Atom(BaseModel):
    text: str = Field(
        description="Single minimal verifiable claim that must appear in a correct system response"
    )
    mode: Literal["extracted", "synthesis"] = Field(
        description="extracted: claim maps directly to a fact in a document | "
                    "synthesis: claim requires combining multiple facts or multi-step reasoning"
    )


class GeneratedQuestion(BaseModel):
    uid: str = Field(description="Assigned after generation, leave empty string")
    type: Literal["n_hop", "fan_in", "bridge", "subgraph", "inconsistency", "irresolvable"] = Field(
        description="Question type")
    hop_count: Optional[int] = Field(None,
                                     description="For n_hop only: number of graph hops required. Null for all other types.")
    question: str = Field(
        description="The question in the corpus language, phrased exactly as a real analyst would ask it")
    answer: str = Field(description="Complete reference answer with all relevant facts and reasoning steps")
    golden_entity_uids: List[str] = Field(description="UIDs of KG entities central to this question")
    golden_fact_uids: List[str] = Field(description="UIDs of value/relation facts from the KG required to answer")
    atoms: List[Atom] = Field(description="Minimal verifiable claims a correct system response must contain")


class GeneratedQuestionSet(BaseModel):
    questions: List[GeneratedQuestion] = Field(description="All generated questions for this batch")


class QuestionGenerationConfig(BaseModel):
    language: str = "Russian"
    max_hops: int = 5
    n_hop_per_level: int = 10
    fan_in_count: int = 10
    bridge_count: int = 10
    subgraph_count: int = 20
    inconsistency_count: int = 10
    irresolvable_count: int = 10

config = QuestionGenerationConfig()

llm = load_llm_lc("gemini3pro")
gen_llm = llm.with_structured_output(GeneratedQuestionSet)


def build_tasks(plan: CorpusPlan, config: QuestionGenerationConfig) -> List[Tuple[str, dict, Optional[int]]]:
    tasks = []

    for n in range(1, config.max_hops + 1):
        tasks.append(("q_n_hop", dict(n=n, count=config.n_hop_per_level)))

    tasks.append(("q_fan_in", dict(count=config.fan_in_count)))
    tasks.append(("q_bridge", dict(count=config.bridge_count)))
    tasks.append(("q_subgraph", dict(count=config.subgraph_count)))
    tasks.append(("q_irresolvable", dict(count=config.irresolvable_count)))

    incons = next((d for d in plan.documents if d.is_inconsistency_doc), None)
    if config.inconsistency_count > 0 and incons:
        tasks.append(("q_inconsistency", dict(
            count=10,
            contradictions_json=json.dumps(
                [c.model_dump() for c in incons.contradictions],
                indent=2, ensure_ascii=False,
            ),
        )))
    return tasks


def plan_summary(p: CorpusPlan):
    return [
        dict(
            name=d.filename,
            description=d.description,
            entitiy_uids=[i.entity_uid for i in d.entity_usages],
            fact_uids=[i.fact_uid for i in d.fact_placements],
            contradictions=[(i.original_fact_uid, i.contradiction_type, i.contradiction_type)
                            for i in d.contradictions if d.is_inconsistency_doc]
        )
        for d in p.documents
    ]


async def generate_batch(base_prompt: str, type_name: str, type_kwargs: dict) -> List[GeneratedQuestion]:
    prompt = base_prompt + "\n\n" + fmt_q_ppt(type_name, **type_kwargs)
    result: GeneratedQuestionSet = await gen_llm.ainvoke([SystemMessage(prompt)])
    return result.questions



async def make_questions(kg: KGGen, plan: CorpusPlan):
    base = fmt_q_ppt(
        "q_base",
        kg_json=kg.model_dump_json(indent=2, ensure_ascii=False),
        plan_summary=plan_summary(plan),
        language="russian",
    )

    batches = build_tasks(plan, config)

    questions = await asyncio.gather(*[generate_batch(base, p_name, kwargs) for p_name, kwargs in batches])
    questions = [q for b in questions for q in b]
    return questions
