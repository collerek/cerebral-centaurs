from typing import Dict, Optional, List

from pydantic import BaseModel

from codejam.server.models.phrase_generator import PhraseDifficulty
from codejam.server.models.user import User


class TurnMessage(BaseModel):
    """Turn related messages."""

    class Config:
        use_enum_values = True

    turn_no: int
    active: bool = True
    level: PhraseDifficulty
    drawer: Optional[str]
    duration: int
    phrase: str
    winner: Optional[str]
    score: Dict[str, int]


class GameMessage(BaseModel):
    """Game related messages."""

    success: bool
    game_id: str
    difficulty: Optional[str]
    turn: Optional[TurnMessage]
    members: Optional[List[str]]
