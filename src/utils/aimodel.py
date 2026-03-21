from typing import Optional

from langchain_openai.chat_models import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from src.utils.config import sys_cfg, LLMCreds


def load_llm_conf(code: str) -> Optional[LLMCreds]:
    if not (llm := sys_cfg.llms.get(code, None)): return None
    if not (prov := sys_cfg.providers.get(llm.provider, None)): return None
    return LLMCreds(
        url=str(prov.url),
        token=prov.token,
        model=llm.model,
        props=llm.props
    )


def load_llm_lc(code: str) -> Optional[BaseChatModel]:
    if not (conf := load_llm_conf(code)): return None
    return ChatOpenAI(
        model=conf.model,
        base_url=conf.url,
        api_key=conf.token,
        **conf.props
    )
