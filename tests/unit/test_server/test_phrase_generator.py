import unittest

from codejam.server.models.phrase_generator import PhraseGenerator, PhraseDifficulty, PhraseCategory


class MyTestCase(unittest.TestCase):
    def test_generates_string_phrase(self):
        self.assertIsInstance(PhraseGenerator.generate_phrase(), str)

    def test_difficulties_work(self):
        for enum in PhraseDifficulty:
            self.assertIsInstance(PhraseGenerator.generate_phrase(difficulty=enum), str)

    def test_categories_work(self):
        for enum in PhraseCategory:
            self.assertIsInstance(PhraseGenerator.generate_phrase(category=enum), str)

    def test_raises_on_invalid_difficulty(self):
        with self.assertRaises(ValueError):
            PhraseGenerator.generate_phrase(difficulty="invalid")


if __name__ == '__main__':
    unittest.main()
