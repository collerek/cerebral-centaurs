from typing import Optional, Union

from pydantic import BaseModel

from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.picture_message import PictureMessage
from codejam.server.interfaces.topics import Topic


class Message(BaseModel):
    """Interface to exchange messages between clients."""

    topic: Topic
    username: str
    game_id: Optional[str]
    value: Optional[Union[PictureMessage, GameMessage, ChatMessage, ErrorMessage]]
