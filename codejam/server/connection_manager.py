from typing import Dict, List

from starlette.websockets import WebSocket

from codejam.server.game import Game
from codejam.server.interfaces.message import Message
from codejam.server.user import User


class ConnectionManager:
    """Manages games connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.active_games: Dict[str, Game] = {}
        self.ids = []

    def get_game(self, game_id: str) -> Game:
        """Get game from active games."""
        if game_id not in self.active_games:
            raise ValueError(f"Game with id: {game_id} does not exist!")
        return self.active_games[game_id]

    async def join_game(self, game_id: str, new_member: User):
        """Accepts the connections and stores it in a list"""
        await self.get_game(game_id=game_id).join(new_member=new_member)

    def leave(self, game_id: str, member: User):
        """Remove the connections from active connections"""
        self.get_game(game_id=game_id).leave(member)

    async def broadcast(self, game_id: str, message: Message):
        """Broadcast the message to all active clients"""
        await self.get_game(game_id=game_id).broadcast(message=message)
