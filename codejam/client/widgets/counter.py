from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class Counter(Label):
    """Counter to count down the duration."""

    a = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = None

    def start(self):
        """Start the counter for a set duration"""
        self.cancel_animation()
        self.anim = Animation(a=0, duration=self.a)

        # TODO: Add explicit test for this
        def finish_callback(animation: Animation, counter: Label):  # pragma: no cover
            counter.text = "FINISHED"

        self.anim.bind(on_complete=finish_callback)
        self.anim.start(self)

    def cancel_animation(self):
        """Cancel counter animation"""
        Animation.cancel_all(self)

    def on_a(self, instance: Widget, value: int):
        """Set text on a change."""
        self.text = str(round(value, 1))
