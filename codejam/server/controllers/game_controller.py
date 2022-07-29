import asyncio
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.exceptions import CannotStartNotOwnGame, GameEnded, NotEnoughPlayers
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations, GameOperations, Topic, TopicEnum

if TYPE_CHECKING:  # pragma: no cover
    from codejam.server.models.game import Game
    from codejam.server.models.user import User


async def delay_wrapper(delay: int, coro: Coroutine):  # pragma: no cover
    """Executes next turn after delay if turn not won."""
    await asyncio.sleep(delay)
    await coro


class GameController(BaseController):
    """Handles messages for GameOperations."""

    def __init__(self, manager: ConnectionManager):
        super().__init__(manager=manager)

    @cached_property
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""
        return {
            GameOperations.JOIN.value: self.join_game,
            GameOperations.CREATE.value: self.create_game,
            GameOperations.END.value: self.end_game,
            GameOperations.START.value: self.start_game,
        }

    async def start_game(self, message: Message):
        """Join existing game for a user."""
        user = self.manager.get_user(message.username)
        game = self.manager.get_game(game_id=message.game_id)
        if user != game.creator:
            raise CannotStartNotOwnGame(
                f"Only {game.creator.username} can start the game {game.secret}"
            )
        game.active = True
        await self.execute_turn(game=game, user=user)

    async def execute_turn(self, game: "Game", user: "User"):
        """Initiates and schedules advancing of the turn if there are enough players."""
        try:
            await self.play_turn(game=game)
            current_turn = game.current_turn
            game.active_turn = asyncio.create_task(
                delay_wrapper(
                    delay=current_turn.duration, coro=self.execute_turn(game=game, user=user)
                )
            )
        except NotEnoughPlayers as e:
            message = Message(
                topic=Topic(type=TopicEnum.ERROR, operation=ErrorOperations.BROADCAST),
                username=game.creator.username,
                game_id=game.secret,
                value=ErrorMessage(exception=e.__class__.__name__, value=str(e)),
            )
            await user.send_message(message=message)

    async def play_turn(self, game: "Game"):
        """Advances the turn and send messages."""
        game.turn()
        current_turn = game.current_turn
        secret_message = Message(
            topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.TURN.value),
            username=game.creator.username,
            game_id=game.secret,
            value=GameMessage(
                success=True,
                game_id=game.secret,
                turn=TurnMessage(
                    turn_no=current_turn.turn_no,
                    level=current_turn.level,
                    drawer=current_turn.drawer.username,
                    duration=current_turn.duration,
                    phrase=current_turn.phrase,
                    score=game.score,
                ),
            ),
        )
        await current_turn.drawer.send_message(message=secret_message)
        hashed_message = secret_message.copy(deep=True)
        hashed_message.value.turn.phrase = "*" * 10
        await self.manager.broadcast(
            game_id=hashed_message.game_id,
            message=hashed_message,
            exclude=[current_turn.drawer],
        )

    async def create_game(self, message: Message):
        """Create a new game for a user."""
        user = self.manager.get_user(message.username)
        difficulty = message.value.difficulty if hasattr(message.value, "difficulty") else None
        game_id = self.manager.register_game(
            creator=user, game_id=message.game_id, difficulty=difficulty
        )
        self.manager.join_game(game_id=game_id, new_member=user)
        message = Message(
            topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.CREATE.value),
            username=user.username,
            game_id=game_id,
            value=GameMessage(success=True, game_id=game_id, difficulty=difficulty),
        )
        await user.send_message(message=message)

    async def join_game(self, message: Message):
        """Join existing game for a user."""
        user = self.manager.get_user(message.username)
        self.manager.join_game(game_id=message.game_id, new_member=user)
        message = Message(
            topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
            username=user.username,
            game_id=message.game_id,
            value=GameMessage(success=True, game_id=message.game_id),
        )
        await self.manager.broadcast(game_id=message.game_id, message=message)
        await self.manager.fill_history(game_id=message.game_id, new_member=user)
        return message.game_id

    async def end_game(self, message: Message):
        """End existing game by creator."""
        raise GameEnded("Game was ended by the creator!")
