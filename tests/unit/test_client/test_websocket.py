from typing import Dict

import pytest

from codejam.client.client import root_widget
from codejam.client.widgets.whiteboard_screen import WhiteBoardScreen
from tests.unit.test_client.mocks import WebsocketMock

URL = f"ws://127.0.0.1:8000/ws/{root_widget.username}"


class Empty:
    ...


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
    screen = WhiteBoardScreen(manager=mocker.Mock(username=root_widget.username, game_id=root_widget.game_id))
    message = "test message"
    screen.message = message
    screen.second_message = message
    if mocked_websockets.refuse_connection:
        with pytest.raises(ConnectionRefusedError):
            await screen.run_websocket()
    else:
        await screen.run_websocket()
    assert screen.received == expected_received
    assert screen.message == expected_message
    assert mocked_websockets.url == expected_url
