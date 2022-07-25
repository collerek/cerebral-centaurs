from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Game related messages."""

    sender: str
    message: str
