from typing import Callable, Dict

from kivy.animation import Animation

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, TopicEnum


class GameEventHandler(BaseEventHandler):
    """Handler for game related events."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_callbacks: Dict[str, Callable[[Message], None]] = {
            GameOperations.CREATE.value: self.game_create,
            GameOperations.JOIN.value: self.game_join,
            GameOperations.START.value: self.game_start,
            GameOperations.TURN.value: self.play_turn,
            GameOperations.WIN.value: self.update_score,
            GameOperations.END.value: self.game_end,
            GameOperations.LEAVE.value: self.leave_game,
        }
        self.callbacks[TopicEnum.GAME.value] = self.game_callbacks

    def cancel_trick(self):
        """Cancel current trick if it's applied"""
        self.cvs.offset_x = self.canvas_initial_offset_x
        self.cvs.offset_y = self.canvas_initial_offset_y
        self.cvs.angle = 0
        self.snail_active = False
        if self.current_trick:
            if isinstance(self.current_trick, Animation):
                self.current_trick.cancel(self.cvs)
            else:
                self.current_trick.cancel()
                if self.pacman_animation:
                    self.pacman_animation.cancel(self)

    def game_create(self, message: Message) -> None:
        """Create game message from other clients"""
        self.manager.game_id = message.value.game_id
        self.ids.score_board.add_joining_player(player=message.username)
        self.ids.score_board.turns_no = message.value.game_length

    def game_join(self, message: Message) -> None:
        """Join game message from other clients"""
        self.ids.score_board.turns_no = message.value.game_length
        for member in message.value.members:
            self.ids.score_board.add_joining_player(player=member)

    def game_start(self, message: Message) -> None:
        """Start game message from other clients"""
        self.manager.game_active = True

    def play_turn(self, message: Message):
        """Play a game turn."""
        self.cvs.canvas.clear()
        self.cancel_trick()
        drawer = message.value.turn.drawer
        client = self.manager.username
        duration = message.value.turn.duration
        self.ids.score_board.update_score(message=message)
        self.ids.score_board.current_turn = message.value.turn.turn_no
        self.ids.counter.a = duration
        self.ids.counter.start()
        self.manager.can_draw = drawer == client
        drawing_person = "your" if client == drawer else drawer
        phrase = message.value.turn.phrase if client == drawer else ""
        action = "draw" if client == drawer else "guess"
        self.current_phrase.text = phrase if client == drawer else ""
        display_popup(
            header="Next turn!",
            title=f"Now is {drawing_person} turn to draw!",
            message=f"You have {duration} seconds to {action}!",
            additional_message=phrase,
        )

    def leave_game(self, message: Message):
        """Handle leaving players, remove them from score board."""
        members = message.value.members
        self.ids.score_board.rebuild_score(players=members)

    def update_score(self, message: Message):
        """Display winner."""
        winner = message.value.turn.winner
        client = self.manager.username
        self.cvs.canvas.clear()
        self.cancel_trick()
        self.current_phrase.text = ""
        self.ids.counter.cancel_animation()
        self.ids.score_board.update_score(message=message)
        self.ids.counter.text = "WAITING FOR START"
        header = "You WON!" if client == winner else f"Player {message.value.turn.winner} WON!"
        display_popup(
            header=header,
            title="The phrase guessed was:",
            message=message.value.turn.phrase,
            additional_message="Next turn will start in 5 seconds!",
        )

    def game_end(self, message: Message):
        """Handle game end event."""
        self.cvs.canvas.clear()
        self.ids.score_board.current_turn = 0
        self.ids.score_board.turns_no = 0
        self.manager.current = "menu_screen"
        self.ids.counter.cancel_animation()
        self.ids.counter.text = "WAITING FOR START"
        self.current_phrase.text = ""
        self.cancel_trick()
        score = message.value.turn.score
        max_score = max(score.values())
        winners = [u for u in score if score[u] == max_score]
        title = "The winner is:" if len(winners) == 1 else "Draw! The winners are:"
        display_popup(
            header="GAME END!",
            title=title,
            message=", ".join(winners),
            additional_message="",
        )
