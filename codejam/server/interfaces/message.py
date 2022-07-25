from typing import Union

from pydantic import BaseModel

from codejam.server.interfaces.picture_message import PictureMessage
from codejam.server.interfaces.topics import Topic


class Message(BaseModel):
    """Interface to exchange messages between clients."""

    topic: Topic
    username: str
    game_id: str
    value: Union[PictureMessage]
