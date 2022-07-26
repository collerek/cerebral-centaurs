from typing import Dict, List

from codejam.server.exceptions import GameNotExist, UserNotExist
from codejam.server.interfaces.message import Message
from codejam.server.models.game import Game
from codejam.server.models.user import User


class ConnectionManager:
    """Manages users and games connections."""

    def __init__(self):
        self.active_connections: List[User] = []
        self.active_games: Dict[str, Game] = {}
        self.ids = []

    async def connect(self, user: User):
        """Accepts the connections and stores it in a list"""
        await user.websocket.accept()
        self.active_connections.append(user)

    def disconnect(self, user: User):
        """Remove the connections from active connections"""
        for game in user.owned_games:
            self.active_games.pop(game.secret)
        self.active_connections.remove(user)

    def get_user(self, username: str) -> User:
        """Get user from active connections by username."""
        user = next((x for x in self.active_connections if x.username == username), None)
        if not user:
            raise UserNotExist(f"User with username: {username} does not exist!")
        return user

    def register_game(self, creator: User) -> str:
        """Get game from active games."""
        game = Game(creator=creator)
        self.active_games[game.secret] = game
        creator.owned_games.append(game)
        return game.secret

    def get_game(self, game_id: str) -> Game:
        """Get game from active games."""
        if game_id not in self.active_games:
            raise GameNotExist(f"Game with id: {game_id} does not exist!")
        return self.active_games[game_id]

    def join_game(self, game_id: str, new_member: User):
        """Accepts the connections and stores it in a list"""
        self.get_game(game_id=game_id).join(new_member=new_member)

    async def fill_history(self, game_id: str, new_member: User):
        """Accepts the connections and stores it in a list"""
        await self.get_game(game_id=game_id).fill_history(new_member=new_member)

    def leave(self, game_id: str, member: User):
        """Remove the connections from active connections"""
        self.get_game(game_id=game_id).leave(member)

    async def broadcast(self, game_id: str, message: Message):
        """Broadcast the message to all active clients"""
        await self.get_game(game_id=game_id).broadcast(message=message)
