from typing import List

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import TopicEnum
from codejam.server.user import User


class Game:
    """Represents a game instance between players."""

    def __init__(self, creator: User, secret: str) -> None:
        self.creator = creator
        self.members: List[User] = []
        self.active_drawers: List[User] = []

        self.secret = secret

        self.current_turn = 0
        self.current_phrase = ""

        self.history: List[Message] = []

    async def broadcast(self, message: Message):
        """Broadcast the message to all active members"""
        for user in self.members:
            if message.topic.type in [TopicEnum.DRAW.value, TopicEnum.CHAT.value]:
                self.history.append(message)
            await user.send_message(message=message)

    async def join(self, new_member: User):
        """Accept the new player and store it in a list"""
        await new_member.websocket.accept()
        for message in self.history:
            await new_member.send_message(message=message)
        self.members.append(new_member)

    def leave(self, member: User):
        """Accept the new player and store it in a list"""
        self.members.remove(member)
