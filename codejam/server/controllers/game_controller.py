import asyncio
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.exceptions import (
    CannotStartNotOwnGame,
    GameAlreadyStarted,
    GameEnded,
    NotEnoughPlayers,
)
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations, GameOperations, Topic, TopicEnum
from codejam.server.models.tricks_generator import TrickGenerator

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
            GameOperations.LEAVE.value: self.leave_game,
        }

    async def start_game(self, message: Message):
        """Join existing game for a user."""
        user = self.manager.get_user(message.username)
        game = self.manager.get_game(game_id=message.game_id)
        if user != game.creator:
            raise CannotStartNotOwnGame(
                f"Only {game.creator.username} can start the game {game.secret}"
            )
        if not game.active:
            game.active = True
            await self.execute_turn(game=game, user=user)
        else:
            raise GameAlreadyStarted()

    async def execute_turn(self, game: "Game", user: "User"):
        """Initiates and schedules advancing of the turn if there are enough players."""
        try:
            await self.play_turn(game=game)
            current_turn = game.current_turn
            game.active_turn = asyncio.create_task(
                delay_wrapper(
                    delay=current_turn.duration,
                    coro=self.execute_turn(game=game, user=user),
                )
            )
            game.active_trick = asyncio.create_task(TrickGenerator(game=game).release_the_kraken())
        except NotEnoughPlayers as e:
            game.active = False
            message = Message(
                topic=Topic(type=TopicEnum.ERROR, operation=ErrorOperations.BROADCAST),
                username=game.creator.username,
                game_id=game.secret,
                value=ErrorMessage(exception=e.__class__.__name__, value=str(e)),
            )
            await self.manager.broadcast(game_id=game.secret, message=message)
        except GameEnded:
            game.active = False
            message = Message(
                topic=Topic(type=TopicEnum.GAME, operation=GameOperations.END),
                username=game.creator.username,
                game_id=game.secret,
                value=GameMessage(
                    success=True,
                    game_id=game.secret,
                    game_length=game.game_length,
                    turn=TurnMessage(
                        turn_no=game.current_turn.turn_no,
                        level=game.difficulty_level,
                        duration=0,
                        phrase="",
                        score=game.score,
                    ),
                ),
            )
            await self.manager.broadcast(game_id=game.secret, message=message)

    async def play_turn(self, game: "Game"):
        """Advances the turn and send messages."""
        if game.active:
            game.turn()
            current_turn = game.current_turn
            secret_message = Message(
                topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.TURN.value),
                username=game.creator.username,
                game_id=game.secret,
                value=GameMessage(
                    success=True,
                    game_id=game.secret,
                    game_length=game.game_length,
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
        game = self.manager.register_game(
            creator=user, game_id=message.game_id, difficulty=difficulty
        )
        self.manager.join_game(game_id=game.secret, new_member=user)
        message = Message(
            topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.CREATE.value),
            username=user.username,
            game_id=game.secret,
            value=GameMessage(
                success=True,
                game_id=game.secret,
                difficulty=difficulty,
                game_length=game.game_length,
            ),
        )
        await user.send_message(message=message)

    async def join_game(self, message: Message):
        """Join existing game for a user."""
        user = self.manager.get_user(message.username)
        game = self.manager.join_game(game_id=message.game_id, new_member=user)
        message = Message(
            topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
            username=user.username,
            game_id=message.game_id,
            value=GameMessage(
                success=True,
                game_id=message.game_id,
                game_length=game.game_length,
                members=self.manager.get_members(message.game_id),
            ),
        )
        await self.manager.broadcast(game_id=message.game_id, message=message)
        await self.manager.fill_history(game_id=message.game_id, new_member=user)
        return message.game_id

    async def leave_game(self, message: Message):
        """Handles player leaving a game."""
        user = self.manager.get_user(message.username)
        game = self.manager.get_game(game_id=message.game_id)
        if user != game.creator:
            self.manager.leave(game_id=game.secret, member=user)
            message = Message(
                topic=Topic(type=TopicEnum.GAME, operation=GameOperations.LEAVE),
                username=user.username,
                game_id=message.game_id,
                value=GameMessage(
                    success=True,
                    game_id=message.game_id,
                    members=self.manager.get_members(game_id=message.game_id),
                ),
            )
            await self.manager.broadcast(game_id=message.game_id, message=message)
            try:
                game.check_if_game_has_enough_players()
            except NotEnoughPlayers as e:
                game.active = False
                raise e
        else:
            game.active = False
            await self.end_game(message=message)

    async def end_game(self, message: Message):
        """End existing game by creator."""
        game = self.manager.get_game(game_id=message.game_id)
        game.active = False
        raise GameEnded("Game was ended by the creator!")
