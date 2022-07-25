from pydantic import BaseModel


class GameMessage(BaseModel):
    """Game related messages."""

    success: bool
    game_id: str
