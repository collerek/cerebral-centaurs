from kivy.clock import Clock

from codejam.client.widgets.whiteboard_tools import InfoPopup


def display_popup(
    header: str,
    title: str,
    message: str,
    additional_message: str,
    auto_dismiss: bool = True,
) -> None:
    """Displays a popup message!"""
    popup = InfoPopup(
        header=header,
        title=title,
        message=message,
        additional_message=additional_message,
    )
    popup.open()
    if auto_dismiss:
        Clock.schedule_once(popup.dismiss, 3)
