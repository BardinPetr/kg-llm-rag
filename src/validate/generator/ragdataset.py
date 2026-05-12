import uuid
from typing import *

from pydantic import Field, BaseModel


class KGRAGClaim(BaseModel):
    type: Literal["claim", "entity"]
    mode: Literal["extracted", "synthesis"]
    claim: str
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))

class KGRAGDatasetQuestion(BaseModel):
    type: str
    is_unanswerable: bool
    is_trick: bool
    question: str
    answer: str
    golden_claims: List[KGRAGClaim] = Field(default_factory=list)


class KGRAGDatasetBlock(BaseModel):
    block_id: str
    block_context: str
    document_names: List[str] = Field(default_factory=list)
    document_contexts: List[str] = Field(default_factory=list)
    questions: List[KGRAGDatasetQuestion] = Field(default_factory=list)


class KGRAGDataset(BaseModel):
    document_blocks: List[KGRAGDatasetBlock] = Field(default_factory=list)
