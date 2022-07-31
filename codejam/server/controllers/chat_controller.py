import asyncio
from functools import cached_property
from typing import Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.controllers.game_controller import GameController
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ChatOperations, GameOperations, Topic, TopicEnum
from codejam.server.models.game import Turn


class ChatController(BaseController):
    """Handles messages for ChatOperations."""

    def __init__(self, manager: ConnectionManager):
        super().__init__(manager=manager)
        self.turn_delay = 5

    @cached_property
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""
        return {ChatOperations.SAY.value: self.say}

    @staticmethod
    def check_if_winning_phrase(current_turn: Turn, message: Message):
        """Check if all words from phrase are in the message."""
        phrase_tokens = current_turn.phrase.lower().split()
        message_tokens = message.value.message.lower().split()
        return all([x in message_tokens for x in phrase_tokens])

    async def check_if_we_have_a_winner(self, message: Message):
        """Check if someone posted the answer in the chat."""
        user = self.manager.get_user(message.username)
        game = self.manager.get_game(game_id=message.game_id)
        current_turn = game.current_turn
        if (
            current_turn
            and self.check_if_winning_phrase(current_turn=current_turn, message=message)
            and current_turn.drawer.username != message.value.sender
        ):
            game.win(user)
            won_message = Message(
                topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.WIN.value),
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
                        winner=user.username,
                    ),
                ),
            )
            await self.manager.broadcast(
                game_id=won_message.game_id,
                message=won_message,
            )
            await self.wait_till_next_turn()
            game_controller = GameController(manager=self.manager)
            await game_controller.execute_turn(game=game, user=user)

    async def wait_till_next_turn(self):  # pragma no cover
        """Introduce delay between rounds."""
        await asyncio.sleep(self.turn_delay)

    def censor_drawer(self, message: Message) -> Message:
        """Removes words from chat that are in the guess phrase."""
        user = self.manager.get_user(message.username)
        game = self.manager.get_game(game_id=message.game_id)
        if game.current_turn and game.current_turn.drawer.username == user.username:
            tokens = [x.lower() for x in game.current_turn.phrase.split()]
            censored = [
                x if x.lower() not in tokens else "<CENSORED>"
                for x in message.value.message.split(" ")
            ]
            message.value.message = " ".join(censored)
        return message

    async def say(self, message: Message):
        """Handles sending the chat message."""
        message = self.censor_drawer(message=message)
        await self.check_if_we_have_a_winner(message=message)
        await self.manager.broadcast(
            game_id=message.game_id,
            message=message,
        )
