from typing import Dict, Optional

from pydantic import BaseModel

from codejam.server.interfaces.topics import GameLevel


class TurnMessage(BaseModel):
    """Turn related messages."""

    class Config:
        use_enum_values = True

    turn_no: int
    active: bool = True
    level: GameLevel
    drawer: Optional[str]
    duration: int
    phrase: str
    winner: Optional[str]
    score: Dict[str, int]


class GameMessage(BaseModel):
    """Game related messages."""

    success: bool
    game_id: str
    turn: Optional[TurnMessage]
