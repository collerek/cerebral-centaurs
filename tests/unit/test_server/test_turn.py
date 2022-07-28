from codejam.server.models.game import Turn
from codejam.server.models.phrase_generator import PhraseGenerator


def test_phrase_is_generated(mocker):
    turn = Turn(turn_no=1, drawer=mocker.Mock(), duration=30)
    phrase = turn.generate_phrase()
    assert isinstance(phrase, str)
    assert phrase in PhraseGenerator.read_phrase_file("medium")
