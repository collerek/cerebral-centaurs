import asyncio

import pytest
from kivy.lang import Builder

from codejam.client.client import WhiteBoardScreen, main_full_path


@pytest.mark.asyncio
async def test_screen_initializes_websocket():
    root_widget = Builder.load_file(f"{main_full_path}")
    print(root_widget.__dir__())
    root_widget.ids.whiteboard.on_pre_enter()
    print(type(root_widget.ws))
    assert isinstance(root_widget.ws, asyncio.Task)
    assert (
        root_widget.ws.get_coro().__qualname__
        == WhiteBoardScreen.run_websocket.__qualname__
    )
