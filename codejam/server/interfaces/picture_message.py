import uuid
from typing import List, Union

from pydantic import BaseModel, Field


class LineData(BaseModel):
    """Interface to exchange line information"""

    line: List[float]
    colour: List[Union[float, int]]
    width: int


class RectData(BaseModel):
    """Interface to exchange rectangle information"""

    pos: List[Union[float, int]]
    colour: List[Union[float, int]]
    size: List[Union[float, int]]


class PictureMessage(BaseModel):
    """Interface to exchange drawable information between clients"""

    draw_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: LineData | RectData
