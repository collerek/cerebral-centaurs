import string
from random import choices
from typing import List

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import TopicEnum
from codejam.server.user import User


class Game:
    """Represents a game instance between players."""

    def __init__(self, creator: User) -> None:
        self.creator = creator
        self.members: List[User] = []
        self.active_drawers: List[User] = []

        self.secret = "".join(choices(string.ascii_letters + string.digits, k=8))

        self.current_turn = 0
        self.current_phrase = ""

        self.history: List[Message] = []

    async def broadcast(self, message: Message):
        """Broadcast the message to all active members"""
        for user in self.members:
            if message.topic.type in [TopicEnum.DRAW.value, TopicEnum.CHAT.value]:
                self.history.append(message)
            await user.send_message(message=message)

    def join(self, new_member: User):
        """Accept the new player and store it in a list"""
        self.members.append(new_member)

    async def fill_history(self, new_member: User):
        """Post all historic messages to new player."""
        for message in self.history:
            await new_member.send_message(message=message)

    def leave(self, member: User):
        """Accept the new player and store it in a list"""
        self.members.remove(member)
