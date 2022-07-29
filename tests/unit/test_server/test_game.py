from codejam.server.models.game import Game, Turn
from codejam.server.models.phrase_generator import PhraseGenerator


def test_phrase_is_generated(mocker):
    game = Game(creator=mocker.MagicMock())
    phrase = game.generate_phrase()
    assert isinstance(phrase, str)
    assert phrase in PhraseGenerator.read_phrase_file("medium")
