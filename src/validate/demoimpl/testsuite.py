from abc import ABC, abstractmethod
from pathlib import Path
from typing import *

from utils.file import do_hash


class RAGTestSuite(ABC):

    @abstractmethod
    async def load(self, documents: List[Path]): ...

    @abstractmethod
    async def ask(self, question: str) -> str: ...

    @staticmethod
    def batch_hash(documents: List[Path]) -> str:
        return do_hash(" ".join([str(i) for i in documents]))
