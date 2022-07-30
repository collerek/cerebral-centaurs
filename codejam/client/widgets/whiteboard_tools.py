from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView


class Instructions(BoxLayout):
    """Instructions rule"""

    _canvas = ObjectProperty(None)


class CanvasTools(BoxLayout):
    """CanvasTools rule"""

    ...


class InfoPopup(ModalView):
    """ErrorPopup"""

    header = StringProperty("")
    title = StringProperty("")
    message = StringProperty("")
    additional_message = StringProperty("")
