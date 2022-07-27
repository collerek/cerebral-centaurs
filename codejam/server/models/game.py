import random
import string
from asyncio import Task
from random import choices
from typing import Dict, List, Optional

from codejam.server.exceptions import NotEnoughPlayers
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameLevel, TopicEnum
from codejam.server.models.user import User


class Turn:
    """Represent game's turn with a new phrase, level and duration."""

    def __init__(
        self,
        turn_no: int,
        drawer: User,
        duration: int,
        level: GameLevel = GameLevel.EASY,
    ):
        self.turn_no = turn_no
        self.level = level
        self.drawer = drawer
        self.duration = duration
        self.phrase = self.generate_phrase()
        self.winner: Optional[User] = None

    def generate_phrase(self):
        """Generates next phrase to guess"""
        return f"Dummy Phrase of level {self.level.value}"


class Game:
    """Represents a game instance between players."""

    def __init__(self, creator: User) -> None:
        self.winner_scores = {GameLevel.EASY: 50, GameLevel.HARD: 100}
        self.allowed_durations = [30, 60]
        self.creator = creator
        self.members: List[User] = []
        self.secret = "".join(choices(string.ascii_letters + string.digits, k=8))
        self.current_turn_no = 0
        self.history: List[Message] = []
        self.turns_history: List[Turn] = []
        self.active = False
        self.active_turn: Optional[Task] = None

    @property
    def current_turn(self) -> Optional[Turn]:
        """Returns current turn played (last from history)."""
        if self.turns_history:
            return self.turns_history[-1]
        return None

    @property
    def score(self) -> Dict:
        """Returns score per player."""
        score: Dict[str, int] = {}
        for player in self.members:
            score[player.username] = 0

        for turn in self.turns_history:
            if turn.winner is not None:
                print(turn.winner.username)
                score[turn.winner.username] = score[turn.winner.username] + self.winner_scores.get(
                    turn.level
                )
        return score

    def win(self, winner: User):
        """Set current turn as won by winner. Cancel scheduled turn change."""
        self.current_turn.winner = winner
        self.active_turn.cancel()

    def turn(self):
        """Advances turn to the next one."""
        if len(self.members) < 3:
            raise NotEnoughPlayers("The game needs at least 3 players!")
        self.current_turn_no += 1
        new_turn = Turn(
            turn_no=self.current_turn_no,
            drawer=random.choice(self.members),
            duration=random.choice(self.allowed_durations),
        )
        self.turns_history.append(new_turn)

    async def broadcast(self, message: Message, exclude: List[User] = None):
        """Broadcast the message to all active members"""
        recipients = self.members if not exclude else [x for x in self.members if x not in exclude]
        for user in recipients:
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
