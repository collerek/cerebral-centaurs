import asyncio
import pathlib
import string
from random import choices

from kivy.app import async_runTouchApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager

from codejam.client.widgets.testcanvas import TestCanvas  # noqa: F401
from codejam.client.widgets.whiteboard import WhiteBoard  # noqa: F401
from codejam.client.widgets.whiteboardscreen import WhiteBoardScreen  # noqa: F401


class RootWidget(ScreenManager):
    """Root widget"""

    username = StringProperty("".join(choices(string.ascii_letters + string.digits, k=8)))
    game_id = StringProperty("randomGame")
    ws = ObjectProperty(None)


root_path = pathlib.Path(__file__).parent.resolve()

main_full_path = root_path.joinpath("rootwidget.kv")

root_widget = Builder.load_file(f"{main_full_path}")


if __name__ == "__main__":  # pragma: no cover

    async def run_app(root):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root, async_lib="asyncio")
        if root.ws:
            root.ws.cancel()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app(root_widget))
    loop.close()
