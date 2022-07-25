import pytest

from codejam.server.connection_manager import ConnectionManager


def test_not_existing_game():
    manager = ConnectionManager()
    with pytest.raises(ValueError) as e:
        manager.get_game("not exist")
    assert "Game with id: not exist does not exist!" in str(e)
