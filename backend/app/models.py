from typing import Optional
from pydantic import BaseModel

class GuessRequest(BaseModel):
    word: str
    target_word: str

class GuessResponse(BaseModel):
    similarity: float
    is_correct: bool
    rank: Optional[int] = None