import uuid

from pydantic import BaseModel, Field


class ErrorMessage(BaseModel):
    """Error related messages."""

    exception: str
    value: str
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
