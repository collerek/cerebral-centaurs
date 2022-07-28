import os
import pathlib
import random
from enum import Enum
from typing import Optional


class PhraseCategory(Enum):
    """Represents a category of phrases."""

    objects = 1
    persons = 2
    verbs = 3


class PhraseDifficulty(Enum):
    """Represents difficulty of a phrase."""

    easy = 1
    medium = 2
    hard = 3


class PhraseGenerator:
    """Generates phrases for the game."""

    @classmethod
    def generate_phrase(
        cls,
        difficulty: PhraseDifficulty = PhraseDifficulty.medium,
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
                case PhraseCategory.objects:
                    return cls.get_random_phrase("objects")
                case PhraseCategory.persons:
                    return cls.get_random_phrase("persons")
                case PhraseCategory.verbs:
                    return cls.get_random_phrase("verbs")
        match difficulty:
            case PhraseDifficulty.easy:
                return cls.get_random_phrase("easy")
            case PhraseDifficulty.medium:
                return cls.get_random_phrase("medium")
            case PhraseDifficulty.hard:
                return cls.get_random_phrase("hard")
        raise ValueError("Invalid difficulty or category")

    @classmethod
    def read_phrase_file(cls, filename: str) -> list[str]:
        """Reads phrase from file."""
        # Remove .txt extension from filename if provided
        filename.rstrip(".txt")

        top_dir = ""
        for parent in pathlib.Path.cwd().parents:
            if str(parent).endswith("cerebral-centaurs"):
                top_dir = str(parent)
                break

        relative_path = f"codejam/server/data/phrases/{filename}.txt"
        file_path = os.path.join(top_dir, relative_path)
        with open(file_path, "r") as f:
            return f.readlines()

    @classmethod
    def get_random_phrase(cls, filename: str) -> str:
        """Returns random phrase."""
        return random.choice(cls.read_phrase_file(filename)).strip()
