import asyncio

import websockets
from kivy.factory import Factory
from kivy.uix.screenmanager import Screen

from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, Topic, TopicEnum


class WhiteBoardScreen(Screen):
    """WhiteBoardScreen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lobby_widget = None

    def on_pre_enter(self) -> None:
        """Called when the screen is about to be shown."""
        if not self.manager.ws:
            self.manager.ws = asyncio.create_task(self.run_websocket())
        if self.manager.create_room:
            try:
                lobby = self.manager.ids.lobby
                if lobby not in self.children:
                    self.add_widget(lobby)
            # TODO: Write test for this path
            except ReferenceError:  # pragma: no cover
                lobby = Factory.Lobby()
                self.add_widget(lobby)
                self.manager.ids["lobby"] = lobby
            """Create new room"""
            self.wb.message = self._prepare_message(
                operation=GameOperations.CREATE, include_difficulty=True
            ).json(models_as_dict=True)
        else:
            """Join existing room"""
            self.remove_lobby()
            self.wb.message = self._prepare_message(operation=GameOperations.JOIN).json(
                models_as_dict=True
            )

    def start_game(self) -> None:
        """Start game"""
        self.wb.message = self._prepare_message(operation=GameOperations.START).json(
            models_as_dict=True
        )
        self.remove_lobby()

    def remove_lobby(self):
        """Remove lobby if exists."""
        try:
            self.remove_widget(self.manager.ids.lobby)
        # TODO: Write test for this path
        except ReferenceError:  # pragma: no cover
            pass

    def _prepare_message(
        self,
        operation: GameOperations,
        include_game_id: bool = True,
        include_difficulty: bool = False,
    ):
        """Helper to create proper messages."""
        difficulty = self.manager.difficulty if include_difficulty else None
        game_id = self.manager.game_id if include_game_id else None
        return Message(
            topic=Topic(type=TopicEnum.GAME, operation=operation),
            username=self.manager.username,
            game_id=game_id,
            value=GameMessage(success=False, game_id=game_id, difficulty=difficulty),
        )

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = "ws://127.0.0.1:8000/ws/{0}".format(self.manager.username)
        try:
            print(url)
            async with websockets.connect(url) as websocket:
                try:
                    while True:
                        if m := self.wb.message:
                            self.wb.message = ""
                            print("sending " + m)
                            await websocket.send(m)
                        try:
                            self.wb.received = await asyncio.wait_for(
                                websocket.recv(), timeout=1 / 60
                            )
                        except asyncio.exceptions.TimeoutError:
                            continue
                        await asyncio.sleep(1 / 60)
                except asyncio.CancelledError as e:
                    print("Loop canceled", e)
                finally:
                    print("Loop finished")
                    self.manager.current = "menu_screen"
        except (ConnectionRefusedError, asyncio.exceptions.TimeoutError) as e:
            print("Connection refused", e)
