from typing import Optional

from dotenv import load_dotenv
from langchain_community.cache import SQLiteCache
from langchain_community.chat_models import ChatDeepInfra
from langchain_core.embeddings import Embeddings
from langchain_core.globals import set_llm_cache
from langchain_core.language_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.embeddings import DeepInfraEmbeddings
from langchain_community.llms.deepinfra import DeepInfra

from src.utils.config import LLMCreds, AppConfig

load_dotenv()

set_llm_cache(SQLiteCache(database_path="/home/petr/study/diploma/.langchain.db"))


def load_llm_conf(code: str) -> Optional[LLMCreds]:
    sys_cfg = AppConfig()
    if not (llm := sys_cfg.llms.get(code, None)): return None
    if not (prov := sys_cfg.providers.get(llm.provider, None)): return None
    return LLMCreds(
        url=str(prov.url),
        token=prov.token,
        model=llm.model,
        type=llm.type,
        props=llm.props,
        provider=llm.provider
    )


def load_llm_lc(code: str, provider: str = None, model: str = None, **kwargs) -> Optional[BaseChatModel | Embeddings]:
    sys_cfg = AppConfig()
    if not (conf := load_llm_conf(code)): return None
    if provider:
        prov = sys_cfg.providers.get(provider, None)
        conf.url = str(prov.url)
        conf.token = prov.token

    if conf.provider == "deepinfra":
        langchain_conf = dict(
            model_id=model or conf.model,
            deepinfra_api_token=conf.token,
        )
        langchain_conf.update(conf.props)
        langchain_conf.update(kwargs)
        print(langchain_conf)
        if conf.type == 'emb':
            return DeepInfraEmbeddings(**langchain_conf)
        else:
            return ChatDeepInfra(**langchain_conf)
    else:
        langchain_conf = dict(
            model=model or conf.model,
            base_url=conf.url,
            api_key=conf.token,
        )
        langchain_conf.update(conf.props)
        langchain_conf.update(kwargs)
        if conf.type == 'emb':
            return OpenAIEmbeddings(**langchain_conf)
        else:
            return ChatOpenAI(**langchain_conf)
