import pathlib
import random
from enum import Enum
from typing import Optional


class ExtEnum(Enum):
    """Extends Enum by list and default"""

    @classmethod
    def list(cls):
        """List of all elements"""
        return list(map(lambda c: c.value, cls))

    @classmethod
    def default(cls):
        """Default value"""
        return cls.list()[0]


class PhraseCategory(ExtEnum):
    """Represents a category of phrases."""

    OBJECTS = "OBJECTS"
    PERSONS = "PERSONS"
    VERBS = "VERBS"


class PhraseDifficulty(ExtEnum):
    """Represents difficulty of a phrase."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class PhraseGenerator:
    """Generates phrases for the game."""

    @classmethod
    def generate_phrase(
        cls,
        difficulty: PhraseDifficulty = PhraseDifficulty.MEDIUM,
        category: Optional[PhraseCategory] = None,
    ) -> str:
        """
        Generates phrase for a turn.

        :param difficulty: difficulty of the phrase.
        PhraseDifficulty enum, choices are: easy, medium (default), hard
        :param category: category of the phrase.
         PhraseCategory enum, choices are: objects, persons, verbs
        """
        if category is not None:
            match category:
                case PhraseCategory.OBJECTS:
                    return cls.get_random_phrase("objects")
                case PhraseCategory.PERSONS:
                    return cls.get_random_phrase("persons")
                case PhraseCategory.VERBS:
                    return cls.get_random_phrase("verbs")
        match difficulty:
            case PhraseDifficulty.EASY:
                return cls.get_random_phrase("easy")
            case PhraseDifficulty.MEDIUM:
                return cls.get_random_phrase("medium")
            case PhraseDifficulty.HARD:
                return cls.get_random_phrase("hard")
        raise ValueError("Invalid difficulty or category")

    @classmethod
    def read_phrase_file(cls, filename: str) -> list[str]:
        """Reads phrase from file."""
        filename.rstrip(".txt")
        server_path = pathlib.Path(__file__).parent.parent.resolve()
        data_folder = server_path.joinpath("data").joinpath("phrases")
        file_path = data_folder.joinpath(f"{filename}.txt").resolve()
        with open(file_path, "r") as f:
            return [x.strip() for x in f.readlines()]

    @classmethod
    def get_random_phrase(cls, filename: str) -> str:
        """Returns random phrase."""
        return random.choice(cls.read_phrase_file(filename))
