import asyncio
import json

import pytest
from kivy.lang import Builder

from codejam.client.client import main_full_path
from codejam.client.widgets.whiteboardscreen import WhiteBoardScreen
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations


@pytest.mark.asyncio
async def test_screen_initializes_websocket():
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.get_screen('whiteboard').on_pre_enter()
    assert isinstance(root_widget.ws, asyncio.Task)
    assert (
        root_widget.ws.get_coro().__qualname__
        == WhiteBoardScreen.run_websocket.__qualname__
    )


@pytest.mark.asyncio
async def test_create_game_prepare_proper_message():
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = True
    root_widget.get_screen('whiteboard').on_pre_enter()
    assert (
        Message(**json.loads(root_widget.get_screen('whiteboard').message)).topic.operation
        == GameOperations.CREATE.value
    )


@pytest.mark.asyncio
async def test_join_game_prepare_proper_message():
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    root_widget.get_screen('whiteboard').on_pre_enter()
    assert (
        Message(**json.loads(root_widget.get_screen('whiteboard').message)).topic.operation
        == GameOperations.JOIN.value
    )

@pytest.mark.asyncio
async def test_start_game_prepare_proper_message():
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    root_widget.get_screen('whiteboard').start_game()
    assert (
        Message(**json.loads(root_widget.get_screen('whiteboard').message)).topic.operation
        == GameOperations.START.value
    )
