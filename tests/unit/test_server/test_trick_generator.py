import pytest

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import Topic, TopicEnum, TrickOperations
from codejam.server.interfaces.trick_message import TrickMessage
from codejam.server.models.tricks_generator import TrickGenerator


def test_valid_trick_is_generated(mocker):
    generator = TrickGenerator(game=mocker.MagicMock())
    assert generator.generate_trick() in TrickOperations


def test_valid_description_is_provided(mocker):
    generator = TrickGenerator(game=mocker.MagicMock())
    assert generator.choose_description(TrickOperations.LANDSLIDE) == (
        "Timbeeeer! Or rather land slide!\n An avalanche swept your drawing canvas!"
    )


def test_valid_delay_is_provided(mocker):
    generator = TrickGenerator(
        game=mocker.MagicMock(current_turn=mocker.MagicMock(duration=10))
    )
    assert 3 <= generator.choose_delay() <= int(10 / 2)


def test_valid_message_is_formatted(mocker):
    mocker.patch(
        "codejam.server.models.tricks_generator.TrickGenerator.generate_trick",
        mocker.MagicMock(return_value=TrickOperations.LANDSLIDE),
    )
    generator = TrickGenerator(game=mocker.MagicMock(secret="secret"))
    assert generator.prepare_trick_message() == Message(
        topic=Topic(type=TopicEnum.TRICK, operation=TrickOperations.LANDSLIDE),
        username="Dirty Goblin",
        game_id="secret",
        value=TrickMessage(
            game_id="secret",
            description="Timbeeeer! Or rather land slide!\n An avalanche swept your drawing canvas!",
        ),
    )


@pytest.mark.asyncio
async def test_releasing_the_kraken(mocker):
    mocker.patch(
        "codejam.server.models.tricks_generator.TrickGenerator.generate_trick",
        mocker.MagicMock(return_value=TrickOperations.LANDSLIDE),
    )
    mocker.patch(
        "codejam.server.models.tricks_generator.TrickGenerator.choose_delay",
        mocker.MagicMock(return_value=0),
    )
    game_mock = mocker.MagicMock(
        secret="secret",
        current_turn=mocker.MagicMock(
            drawer=mocker.MagicMock(send_message=mocker.AsyncMock())
        ),
    )
    generator = TrickGenerator(game=game_mock)
    await generator.release_the_kraken()
    game_mock.current_turn.drawer.send_message.assert_called_once_with(
        Message(
            topic=Topic(type=TopicEnum.TRICK, operation=TrickOperations.LANDSLIDE),
            username="Dirty Goblin",
            game_id="secret",
            value=TrickMessage(
                game_id="secret",
                description="Timbeeeer! Or rather land slide!\n An avalanche swept your drawing canvas!",
            ),
        )
    )
