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
            self.manager.ids.whiteboard.wb.message = Message(
                topic=Topic(type=TopicEnum.GAME, operation=GameOperations.CREATE),
                username=self.manager.username,
                game_id=None,
                value=GameMessage(success=False, game_id=self.manager.game_id),
            ).json(models_as_dict=True)
        else:
            """Join existing room"""
            self.manager.ids.whiteboard.wb.message = Message(
                topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
                username=self.manager.username,
                game_id=self.manager.game_id,
                value=GameMessage(success=False, game_id=self.manager.game_id),
            ).json(models_as_dict=True)

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
        except (ConnectionRefusedError, asyncio.exceptions.TimeoutError) as e:
            print("Connection refused", e)


class JoinScreen(Screen):
    """Join screen."""

    pass


class MenuScreen(Screen):
    """Menu screen"""

    pass
