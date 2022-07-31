import re

from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput


class Instructions(BoxLayout):
    """Instructions rule"""

    _canvas = ObjectProperty(None)


class InfoPopup(ModalView):
    """ErrorPopup"""

    header = StringProperty("")
    title = StringProperty("")
    message = StringProperty("")
    additional_message = StringProperty("")


class FilteredTextInput(TextInput):
    """Game Buttons on menu screen"""

    def insert_text(self, substring: str, from_undo: bool = False):
        """Filter text to allow only alpha numeric w/o spaces"""
        s = re.sub(r"[^A-Za-z0-9]+", "", substring)
        return super().insert_text(s, from_undo=from_undo)
