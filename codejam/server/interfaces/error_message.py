from pydantic import BaseModel


class ErrorMessage(BaseModel):
    """Error related messages."""

    exception: str
    value: str
