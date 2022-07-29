from .chat_handler import ChatEventHandler
from .draw_handler import DrawEventHandler
from .error_handler import ErrorEventHandler
from .game_handler import GameEventHandler


class EventHandler(ErrorEventHandler, ChatEventHandler, DrawEventHandler, GameEventHandler):
    """Combines all handlers into one base class."""
