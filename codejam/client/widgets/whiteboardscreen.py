import asyncio

import websockets
from kivy.uix.screenmanager import Screen

from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, Topic, TopicEnum


class WhiteBoardScreen(Screen):
    """WhiteBoardScreen"""

    def on_pre_enter(self) -> None:
        """Called when the screen is about to be shown."""
        if not self.manager.ws:
            self.manager.ws = asyncio.create_task(self.run_websocket())
        if self.manager.create_room:
            """Create new room"""
            self.wb.message = self._prepare_message(operation=GameOperations.CREATE).json(
                models_as_dict=True
            )
        else:
            """Join existing room"""
            if "lobby" in self.manager.ids:
                self.remove_widget(self.manager.ids.lobby)
            self.wb.message = self._prepare_message(operation=GameOperations.JOIN).json(
                models_as_dict=True
            )

    def start_game(self) -> None:
        """Start game"""
        self.wb.message = self._prepare_message(operation=GameOperations.START).json(
            models_as_dict=True
        )
        self.remove_widget(self.manager.ids.lobby)

    def _prepare_message(self, operation: GameOperations, include_game_id: bool = True):
        """Helper to create proper messages."""
        game_id = self.manager.game_id if include_game_id else None
        return Message(
            topic=Topic(type=TopicEnum.GAME, operation=operation),
            username=self.manager.username,
            game_id=game_id,
            value=GameMessage(success=False, game_id=game_id),
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
