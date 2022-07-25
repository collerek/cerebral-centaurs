from typing import List, Union

from pydantic import BaseModel


class LineData(BaseModel):
    """Interface to exchange line information"""

    line: List[float]
    colour: List[Union[float, int]]


class PictureMessage(BaseModel):
    """Interface to exchange drawable information between clients"""

    data: LineData
