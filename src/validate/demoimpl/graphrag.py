from functools import partial
from pathlib import Path
from typing import List

from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.lightrag import LightRAG
from raganything import RAGAnything, RAGAnythingConfig
from tqdm import tqdm

from utils.aimodel import load_llm_conf
from validate.demoimpl.testsuite import RAGTestSuite

embeddings = load_llm_conf("test-embeddings")
llm = load_llm_conf("test-llm")


def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    return openai_complete_if_cache(
        llm.model,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=llm.token,
        base_url=llm.url,
        **kwargs,
    )


embedding_func = EmbeddingFunc(
    embedding_dim=1536,
    max_token_size=8192,
    func=partial(
        openai_embed.func,
        model=embeddings.model,
        api_key=embeddings.token,
        base_url=embeddings.url,
    ),
)


class OtherGraphRAG(RAGTestSuite):
    async def load(self, documents: List[Path]):
        doc_hash = self.batch_hash(documents)
        lightrag_working_dir = f"./light_rag/{doc_hash}"
        config = RAGAnythingConfig(
            parser="docling"
        )
        lightrag_instance = LightRAG(
            working_dir=lightrag_working_dir,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
            top_k=10
        )
        await lightrag_instance.initialize_storages()
        await initialize_pipeline_status()
        self.rag = RAGAnything(
            lightrag=lightrag_instance,
            config=config,
        )
        output_dir = f"{lightrag_working_dir}/output"
        if not Path(output_dir).exists():
            for i in tqdm(documents):
                await self.rag.process_document_complete(str(i), output_dir=output_dir)

    async def ask(self, question: str) -> str:
        return await self.rag.aquery(question, mode="hybrid")

