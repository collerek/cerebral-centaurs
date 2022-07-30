from pydantic import BaseModel


class TrickMessage(BaseModel):
    """Trick related messages."""

    game_id: str
    description: str
