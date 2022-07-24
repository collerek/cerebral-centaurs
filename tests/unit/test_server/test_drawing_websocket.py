from typing import Dict

import pytest
from starlette.testclient import TestClient

from codejam.server import app


@pytest.fixture
def test_data() -> Dict:
    return {
        "line": [0, 1, 1, 1],
        "colour": [0, 0, 0, 1]
    }


@pytest.fixture
def test_client() -> int:
    return 1


def test_websocket(test_client: int, test_data: Dict):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(test_data)
        data = websocket.receive_json()
        assert data == {"client_id": test_client, "data": test_data}
