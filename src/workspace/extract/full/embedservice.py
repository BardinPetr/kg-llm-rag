from typing import List

from utils.aimodel import load_llm_lc


class EmbeddingService:
    MX_SZ = 4096

    def __init__(self, model_code="emb"):
        self._model = load_llm_lc(model_code)
        self._size = len(self._model.embed_query("test"))
        print(self._size)
        self._pad = [0.0] * (EmbeddingService.MX_SZ - self._size)

    def embed(self, text: str) -> List[float]:
        return self._model.embed_query(text) + self._pad

    def embed_all(self, texts: List[str]) -> List[List[float]]:
        return [i + self._pad for i in self._model.embed_documents(texts)]
