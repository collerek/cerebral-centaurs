import asyncio

import pytest

from codejam.client.client import client_id, run_websocket


@pytest.fixture()
def mocked_websockets(mocker):
    web_socket_mock = WebsocketMock()
    mocker.patch("codejam.client.client.websockets", web_socket_mock)
    return web_socket_mock


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
async def test_websockets(mocker, mocked_websockets):
    message = "test message"
    root_mock = mocker.Mock(message=message)
    await run_websocket(widget=root_mock)

    assert root_mock.received == message
    assert root_mock.message == ""
    assert mocked_websockets.url == f"ws://127.0.0.1:8000/ws/{client_id}"


@pytest.mark.asyncio
async def test_websockets_timeout(mocker, mocked_websockets):
    mocked_websockets.sleep = True
    message = "test message"
    root_mock = mocker.Mock(message=message)
    await run_websocket(widget=root_mock)

    assert root_mock.received == message
    assert root_mock.message == ""
    assert mocked_websockets.url == f"ws://127.0.0.1:8000/ws/{client_id}"


@pytest.mark.asyncio
async def test_websockets_refuse_connection(mocker, mocked_websockets):
    mocked_websockets.refuse_connection = True
    message = "test message"
    root_mock = mocker.Mock(message=message)
    await run_websocket(widget=root_mock)
    assert root_mock.message == message
    assert isinstance(root_mock.received, mocker.Mock)
    assert mocked_websockets.url == ""


@pytest.mark.asyncio
async def test_websockets_cancel_loop(mocker, mocked_websockets):
    mocked_websockets.cancel = True
    message = "test message"
    root_mock = mocker.Mock(message=message)
    await run_websocket(widget=root_mock)
    assert root_mock.message == ""
    assert isinstance(root_mock.received, mocker.Mock)
    assert mocked_websockets.url == f"ws://127.0.0.1:8000/ws/{client_id}"
