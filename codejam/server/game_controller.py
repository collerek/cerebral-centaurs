from typing import Any, Callable, Coroutine, Dict, cast

from codejam.server.connection_manager import ConnectionManager
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, Topic, TopicEnum


class GameController:
    """Handles messages for GameOperations."""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.dispatch_schema: Dict[
            str, Callable[[Message], Coroutine[Any, Any, Any]]
        ] = {
            GameOperations.JOIN.value: self.join_game,
            GameOperations.CREATE.value: self.create_game,
        }

    async def dispatch(self, message: Message):
        """Dispatch controller operations."""
        callback = self.dispatch_schema[cast(str, message.topic.operation)]
        return await callback(message)

    async def create_game(self, message: Message):
        """Create a new game for a user."""
        user = self.manager.get_user(message.username)
        game_id = self.manager.register_game(creator=user)
        self.manager.join_game(game_id=game_id, new_member=user)
        message = Message(
            topic=Topic(
                type=TopicEnum.GAME.value, operation=GameOperations.CREATE.value
            ),
            username=user.username,
            game_id=game_id,
            value=GameMessage(success=True, game_id=game_id),
        )
        await user.send_message(message=message)
        return game_id

    async def join_game(self, message: Message):
        """Join existing game for a user."""
        user = self.manager.get_user(message.username)
        self.manager.join_game(game_id=message.game_id, new_member=user)
        message = Message(
            topic=Topic(type=TopicEnum.GAME.value, operation=GameOperations.JOIN.value),
            username=user.username,
            game_id=message.game_id,
            value=GameMessage(success=True, game_id=message.game_id),
        )
        await user.send_message(message=message)
        await self.manager.fill_history(game_id=message.game_id, new_member=user)
        return message.game_id
