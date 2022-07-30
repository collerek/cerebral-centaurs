import random
import string
from asyncio import Task
from random import choices
from typing import Dict, List, Optional

from codejam.server.exceptions import GameEnded, NotEnoughPlayers
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import TopicEnum
from codejam.server.models.phrase_generator import PhraseDifficulty, PhraseGenerator
from codejam.server.models.user import User


class Turn:
    """Represent game's turn with a new phrase, level and duration."""

    def __init__(
        self,
        turn_no: int,
        drawer: User,
        duration: int,
        phrase: str,
        level: PhraseDifficulty = PhraseDifficulty.MEDIUM,
    ):
        self.turn_no = turn_no
        self.level = level
        self.drawer = drawer
        self.duration = duration
        self.phrase = phrase
        self.winner: Optional[User] = None


class Game:
    """Represents a game instance between players."""

    def __init__(self, creator: User, game_id: str = None, difficulty: str = None) -> None:
        self.winner_scores = {
            PhraseDifficulty.EASY: 50,
            PhraseDifficulty.MEDIUM: 100,
            PhraseDifficulty.HARD: 50,
        }
        self.allowed_durations = [30, 60]
        self.creator = creator
        self.members: List[User] = []
        self.secret = game_id or "".join(choices(string.ascii_letters + string.digits, k=8))
        self.current_turn_no = 0
        self.history: List[Message] = []
        self.turns_history: List[Turn] = []
        self.active = False
        self.active_turn: Optional[Task] = None
        self.active_trick: Optional[Task] = None
        self.difficulty = difficulty
        self.game_length = self.get_number_of_turns()

        self._last_phrase: str = ""
        self._last_drawer: Optional[User] = None

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
            if turn.winner is not None and turn.winner.username in score:
                score[turn.winner.username] = score[turn.winner.username] + self.winner_scores.get(
                    turn.level
                )
        return score

    @property
    def difficulty_level(self) -> PhraseDifficulty:
        """Return set or default difficulty level."""
        return PhraseDifficulty(self.difficulty) if self.difficulty else PhraseDifficulty.MEDIUM

    def win(self, winner: User) -> None:
        """Set current turn as won by winner. Cancel scheduled turn change."""
        self.current_turn.winner = winner
        if self.active_turn:
            self.active_turn.cancel()
        if self.active_trick:
            self.active_trick.cancel()

    def check_if_game_has_enough_players(self) -> None:
        """Check if minimum number of players is filled."""
        if len(self.members) < 3:
            raise NotEnoughPlayers("The game needs at least 3 players!")

    @staticmethod
    def get_number_of_turns() -> int:
        """Get game length as random int 3-15."""
        return random.randint(3, 15)

    def turn(self) -> None:
        """Advances turn to the next one."""
        self.check_if_game_has_enough_players()
        self.current_turn_no += 1
        if self.current_turn_no > self.game_length:
            raise GameEnded()
        new_turn = Turn(
            turn_no=self.current_turn_no,
            drawer=self.get_next_drawer(),
            duration=random.choice(self.allowed_durations),
            phrase=self.generate_phrase(),
            level=self.difficulty_level,
        )
        self.turns_history.append(new_turn)

    def get_next_drawer(self) -> User:
        """Chooses next drawer, must differ than the last one"""
        drawer = random.choice(self.members)
        while drawer == self._last_drawer:  # pragma: no cover
            drawer = random.choice(self.members)
        self._last_drawer = drawer
        return drawer

    def generate_phrase(self) -> str:
        """Generates next phrase to guess, must differ than the last one"""
        new_phrase = PhraseGenerator.generate_phrase(difficulty=self.difficulty_level)
        while new_phrase == self._last_phrase:  # pragma: no cover
            new_phrase = PhraseGenerator.generate_phrase(difficulty=self.difficulty_level)
        self._last_phrase = new_phrase
        return new_phrase

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
        self.score.pop(member.username, None)
        if member in self.members:
            self.members.remove(member)
