import asyncio
import pathlib
import string
from random import choices

from kivy.app import async_runTouchApp
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager

from codejam.client.widgets import *  # noqa: F401 F403


class RootWidget(ScreenManager):
    """Root widget"""

    create_room = BooleanProperty(False)
    game_active = BooleanProperty(False)
    can_draw = BooleanProperty(False)
    difficulty = StringProperty("")
    username = StringProperty("".join(choices(string.ascii_letters + string.digits, k=8)))
    game_id = StringProperty("".join(choices(string.ascii_letters + string.digits, k=8)))
    ws = ObjectProperty(None, allownone=True)


root_path = pathlib.Path(__file__).parent.resolve()
main_full_path = root_path.joinpath("rootwidget.kv")
root_widget = Builder.load_file(f"{main_full_path}")


if __name__ == "__main__":  # pragma: no cover

    async def run_app(root):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root, async_lib="asyncio")
        if root.ws:
            root.ws.cancel()

    asyncio.run(run_app(root_widget))
