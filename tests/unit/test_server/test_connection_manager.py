import pytest

from codejam.server.connection_manager import ConnectionManager
from codejam.server.exceptions import GameNotExist, UserNotExist


def test_not_existing_game():
    manager = ConnectionManager()
    with pytest.raises(GameNotExist) as e:
        manager.get_game("not exist")
    assert "Game with id: not exist does not exist!" in str(e)


def test_not_existing_user():
    manager = ConnectionManager()
    with pytest.raises(UserNotExist) as e:
        manager.get_user("not exist")
    assert "User with username: not exist does not exist!" in str(e)
