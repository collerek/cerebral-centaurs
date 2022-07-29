import pytest

from codejam.server.models.phrase_generator import (
    PhraseCategory,
    PhraseDifficulty,
    PhraseGenerator,
)


def test_generates_string_phrase():
    assert isinstance(PhraseGenerator.generate_phrase(), str)


def test_difficulties_work():
    for enum in PhraseDifficulty:
        assert isinstance(PhraseGenerator.generate_phrase(difficulty=enum), str)


def test_categories_work():
    for enum in PhraseCategory:
        assert isinstance(PhraseGenerator.generate_phrase(category=enum), str)


def test_raises_on_invalid_difficulty():
    with pytest.raises(ValueError):
        PhraseGenerator.generate_phrase(difficulty="invalid")
