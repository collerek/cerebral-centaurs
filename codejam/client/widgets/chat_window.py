import pathlib

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ChatOperations, Topic, TopicEnum


class Chat(FloatLayout):
    """Chat rule"""

    message = StringProperty("")
    sender = StringProperty("")


class ChatWindow(BoxLayout):
    """ChatWindow rule"""

    def add_message(self, message: str, sender: str = None, propagate: bool = True) -> None:
        """Add message to chat window."""
        self.ids.chat_box.add_widget(
            Chat(message=message, sender=sender or self.screen.manager.username)
        )
        if propagate:
            self.send_message(message)

    def send_message(self, message: str) -> None:
        """Send message to server."""
        self.screen.message = self._prepare_message(message).json(models_as_dict=True)

    def _prepare_message(self, message: str) -> Message:
        """Prepare message to send to server."""
        return Message(
            topic=Topic(type=TopicEnum.CHAT, operation=ChatOperations.SAY),
            username=self.screen.manager.username,
            game_id=self.screen.manager.game_id,
            value=ChatMessage(sender=self.screen.manager.username, message=message),
        )


root_path = pathlib.Path(__file__).parent.resolve()
Builder.load_file(f'{root_path.joinpath("chat_window.kv")}')
