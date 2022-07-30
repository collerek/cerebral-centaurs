from .chat_handler import ChatEventHandler
from .draw_handler import DrawEventHandler
from .error_handler import ErrorEventHandler
from .game_handler import GameEventHandler
from .trick_handler import TrickEventHandler


class EventHandler(
    ErrorEventHandler, ChatEventHandler, DrawEventHandler, GameEventHandler, TrickEventHandler
):
    """Combines all handlers into one base class."""
