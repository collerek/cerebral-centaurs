class WhiteBoardException(Exception):
    """Base application exception."""


class GameNotStarted(WhiteBoardException):
    """Raised when user try to draw before joining a game."""


class GameAlreadyStarted(WhiteBoardException):
    """Raised when user try to draw before joining a game."""


class NotAllowedOperation(WhiteBoardException):
    """Raised when user try to draw before joining a game."""


class GameEnded(WhiteBoardException):
    """Raised for other users when creator ends the game."""


class GameNotExist(WhiteBoardException):
    """Raised when game with given game_id does not exist."""


class UserNotExist(WhiteBoardException):
    """Raised when user with given username does not exist."""


class UserAlreadyExists(WhiteBoardException):
    """Raised when user with given username does not exist."""


class NotEnoughPlayers(WhiteBoardException):
    """Raised when user want to start a game with < 3 players."""


class CannotStartNotOwnGame(WhiteBoardException):
    """Raised when user want to start a game with < 3 players."""
