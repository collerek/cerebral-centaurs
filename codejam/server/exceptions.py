class WhiteBoardException(Exception):
    """Base application exception."""


class GameNotStarted(WhiteBoardException):
    """Raised when user try to draw before joining a game."""


class GameEnded(WhiteBoardException):
    """Raised for other users when creator ends the game."""
