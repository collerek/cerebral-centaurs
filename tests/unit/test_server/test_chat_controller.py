from codejam.server.controllers.chat_controller import ChatController
from codejam.server.interfaces.message import Message


def test_censoring_message(chat_message: Message, mocker):
    manager = mocker.MagicMock()
    game = mocker.MagicMock()
    game.current_turn = mocker.MagicMock(
        phrase="forbiDden", drawer=mocker.MagicMock(username="client")
    )
    manager.get_game = mocker.MagicMock(return_value=game)
    manager.get_user = mocker.MagicMock(
        return_value=mocker.MagicMock(username="client")
    )
    chat_controller = ChatController(manager=manager)
    chat_message.value.message = "Test Forbidden word"
    chat_message.username = "client"
    message = chat_controller.censor_drawer(chat_message)
    assert message.value.message == "Test <CENSORED> word"
