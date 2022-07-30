import pathlib

from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from codejam.server.interfaces.message import Message


class Score(FloatLayout):
    """Score of a single player"""

    player = StringProperty("")
    score = NumericProperty(0)


class ScoreBoard(BoxLayout):
    """Score Board keeping scores of all players."""

    def update_score(self, message: Message) -> None:
        """Update score based on TURN message."""
        score_dict = message.value.turn.score
        for player, score in score_dict.items():
            self.upsert_score(player=player, score=score)

    def upsert_score(self, player: str, score: int):
        """Updates/insert score for a pplayer."""
        if player not in self.ids:
            self._add_score(player=player, score=score)
        else:
            score_widget = self.ids[player]
            score_widget.score = score

    def add_joining_player(self, player: str):
        """Adds player to scoreboard on join."""
        self.upsert_score(player=player, score=0)

    def _add_score(self, player: str, score: int):
        """Add score widget."""
        score_widget = Score(player=player, score=score)
        self.ids.scores.add_widget(score_widget)
        self.ids[player] = score_widget


root_path = pathlib.Path(__file__).parent.resolve()
Builder.load_file(f'{root_path.joinpath("scoreboard.kv")}')
