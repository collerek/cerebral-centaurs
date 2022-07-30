from typing import Optional, Union

from pydantic import BaseModel, validator

from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.picture_message import PictureMessage
from codejam.server.interfaces.topics import Topic, TopicEnum
from codejam.server.interfaces.trick_message import TrickMessage


class Message(BaseModel):
    """Interface to exchange messages between clients."""

    topic: Topic
    username: str
    game_id: Optional[str]
    value: Optional[Union[PictureMessage, GameMessage, ChatMessage, ErrorMessage, TrickMessage]]

    @validator("value")
    def operation_match_type(cls, v, values, **kwargs):
        """Verifies that provided operation is of a correct type."""
        expected_messages = {
            TopicEnum.GAME.value: GameMessage,
            TopicEnum.DRAW.value: PictureMessage,
            TopicEnum.CHAT.value: ChatMessage,
            TopicEnum.ERROR.value: ErrorMessage,
            TopicEnum.TRICK.value: TrickMessage,
        }
        topic = values.get("topic")
        if topic is None:
            raise ValueError("Invalid topic type and operation provided!")
        expected_message = expected_messages.get(topic.type)
        if not expected_message or (v is not None and not isinstance(v, expected_message)):
            raise ValueError(f"Not allowed message value for {topic.type}")
        return v
