from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware, ToolRetryMiddleware, \
    ModelRetryMiddleware
from langchain_core.messages import HumanMessage

from utils.aimodel import load_llm_lc
from utils.prompt import sprompt
from search.search_tools import *


llm = load_llm_lc("gemini3pro")

def agent():
    return create_agent(
        model=llm,
        tools=[
            load_ontology,
            entity_search,
            entity_value_search,
            describe_entities,
            describe_facts,
            get_proofs,
            path_search,
            get_type_info,
            fallback_naive_rag,
        ],
        system_prompt=sprompt("search", "main"),
        middleware=[
            ModelRetryMiddleware(
                max_retries=20,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
            ToolRetryMiddleware(
                max_retries=5,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
            ModelCallLimitMiddleware(
                run_limit=50,
                exit_behavior="end",
            ),
            ToolCallLimitMiddleware(
                run_limit=30,
                exit_behavior="end",
            ),
        ]
    )


def kgq_ask(question):
    logger.info(f"[ASK] {question}")
    out = agent().invoke(dict(messages=[HumanMessage(question)]))
    out = out['messages'][-1].content
    logger.info(f"[ANSWER]\n{out}\n[END]\n")
    return out
