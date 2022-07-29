import asyncio
from typing import Dict

import pytest

from codejam.client.client import root_widget
from codejam.client.widgets.whiteboard_screen import WhiteBoardScreen

URL = f"ws://127.0.0.1:8000/ws/{root_widget.username}"


@pytest.fixture()
def mocked_websockets(mocker):
    web_socket_mock = WebsocketMock()
    mocker.patch("codejam.client.widgets.whiteboard_screen.websockets", web_socket_mock)
    return web_socket_mock


class Empty:
    ...


class WebsocketMock:
    def __init__(self):
        self.sleep = False
        self.refuse_connection = False
        self.cancel = False
        self.messages = []
        self.url = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return self

    def connect(self, url: str):
        if self.refuse_connection:
            raise ConnectionRefusedError()
        self.url = url
        return self

    async def send(self, value: str):
        self.messages.append(value)

    async def recv(self):
        if self.cancel:
            raise asyncio.CancelledError
        if self.sleep:
            self.sleep = False
            raise asyncio.exceptions.TimeoutError
        return self.messages.pop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attributes, expected_message, expected_received, expected_url",
    (
        ({}, "", "test message", URL),
        ({"sleep": True}, "", "test message", URL),
        ({"cancel": True}, "", "", URL),
        ({"refuse_connection": True}, "test message", "", ""),
    ),
    ids=[
        "Normal execution",
        "Reaching recv() TimeoutError",
        "Connection cancelled",
        "Connection refused",
    ],
)
async def test_websockets(
    mocker,
    mocked_websockets: WebsocketMock,
    attributes: Dict,
    expected_message: str,
    expected_received: str,
    expected_url: str,
):
    if attributes:
        for key, value in attributes.items():
            setattr(mocked_websockets, key, value)
    screen = WhiteBoardScreen(manager=mocker.Mock(username=root_widget.username))
    message = "test message"
    screen.message = message
    if mocked_websockets.refuse_connection:
        with pytest.raises(ConnectionRefusedError):
            await screen.run_websocket()
    else:
        await screen.run_websocket()
    assert screen.received == expected_received
    assert screen.message == expected_message
    assert mocked_websockets.url == expected_url
