from enum import Enum
from typing import *

from pydantic import BaseModel


class EDedupTaskOption(BaseModel):
    uid: str
    variant: str
    facts: str


class EDedupTask(BaseModel):
    target_uid: str
    target: str
    options: List[EDedupTaskOption]


class EDedupTasks(BaseModel):
    tasks: List[EDedupTask]


class EDedupConfidence(str, Enum):
    EXACT = "exact"
    HIGH = "high"
    LOW = "low"
    NONE = "none"


class EDedupResult(BaseModel):
    target_uid: str
    matched_option_uid: Optional[str] = None
    confidence: EDedupConfidence
    reasoning: str


class EDedupResults(BaseModel):
    results: List[EDedupResult]


