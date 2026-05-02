from typing import List

from utils.aimodel import load_llm_lc
from db.store import cache_get, cache_put
from loguru import logger


class EmbeddingService:
    MX_SZ = 4096

    def __init__(self, model_code="emb"):
        self._model = load_llm_lc(model_code)
        self._size = None

    @property
    def _pad(self):
        if self._size is None:
            self._size = len(self._model.embed_query("test"))
        return [0.0] * (EmbeddingService.MX_SZ - self._size)

    def embed(self, text: str) -> List[float]:
        return self._model.embed_query(text) + self._pad

    def embed_all(self, texts: List[str]) -> List[List[float]]:
        cache_hit, to_embed = cache_get(texts, "embed")
        embedded = {k: (e + self._pad) for k, e in zip(to_embed, self._model.embed_documents(to_embed))}
        cache_put(embedded, "embed")
        logger.info(f"Batch embedding: hit={len(cache_hit)} miss={len(to_embed)}")
        return [
            cache_hit.get(i, None) or embedded.get(i, None)
            for i in texts
        ]
