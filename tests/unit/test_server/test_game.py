from codejam.server.models.game import Game, Turn
from codejam.server.models.phrase_generator import PhraseDifficulty, PhraseGenerator


def test_phrase_is_generated(mocker):
    game = Game(creator=mocker.MagicMock())
    phrase = game.generate_phrase()
    assert isinstance(phrase, str)
    assert phrase in PhraseGenerator.read_phrase_file("medium")


def test_difficulty_level(mocker):
    game = Game(creator=mocker.MagicMock(), difficulty=PhraseDifficulty.HARD.value)
    phrase = game.generate_phrase()
    assert isinstance(phrase, str)
    assert phrase in PhraseGenerator.read_phrase_file("hard")

    game.members.append(mocker.MagicMock())
    game.members.append(mocker.MagicMock())
    game.members.append(mocker.MagicMock())

    game.turn()
    assert game.current_turn.level == game.difficulty_level
