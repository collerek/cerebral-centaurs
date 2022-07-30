import asyncio
import json

import pytest
import websockets.exceptions
from kivy.lang import Builder

from codejam.client.client import main_full_path
from codejam.client.widgets.whiteboard_screen import WhiteBoardScreen
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations
from tests.unit.test_client.mocks import WebsocketMock


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


@pytest.mark.asyncio
async def test_task_raises_connection_error_handler(mocker):
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    task = mocker.AsyncMock(
        result=mocker.MagicMock(side_effect=[ConnectionRefusedError()])
    )
    root_widget.ids.wbs.task_callback(task)


@pytest.mark.asyncio
async def test_task_raises_arbitrary_error_handler(mocker):
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    task = mocker.AsyncMock(result=mocker.MagicMock(side_effect=[ImportError()]))
    root_widget.ids.wbs.task_callback(task)


@pytest.mark.asyncio
async def test_task_raises_cancel_error_handler(mocker):
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    task = mocker.AsyncMock(
        result=mocker.MagicMock(side_effect=[asyncio.CancelledError()])
    )
    root_widget.ids.wbs.task_callback(task)

@pytest.mark.asyncio
async def test_task_raises_websocket_connection_closed_error_handler(mocker):
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    task = mocker.AsyncMock(
        result=mocker.MagicMock(side_effect=[websockets.exceptions.ConnectionClosedError(rcvd=None, sent=None)])
    )
    root_widget.ids.wbs.task_callback(task)


@pytest.mark.asyncio
async def test_task_returns_ok_handler(mocker):
    root_widget = Builder.load_file(f"{main_full_path}")
    root_widget.create_room = False
    task = mocker.AsyncMock(result=mocker.MagicMock(side_effect=[2]))
    result = root_widget.ids.wbs.task_callback(task)
    assert result == 2


@pytest.mark.asyncio
async def test_actual_websocket_runner(mocked_websockets: WebsocketMock):
    root_widget = Builder.load_file(f"{main_full_path}")
    await root_widget.ids.wbs.run_websocket()
    assert mocked_websockets.url == f"ws://127.0.0.1:8000/ws/{root_widget.username}"
