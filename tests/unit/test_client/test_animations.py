from kivy.base import EventLoop
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget


class AnimationTestCase(GraphicUnitTest):

    def test_entering_left(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.pos = (0, 0)

        self._win.mouse_pos = [self._win.width * 0.02, self._win.height / 2]
        self.advance_frames(45)
        assert wb_screen.left_enter
        assert wb_screen.left_x == 0.2

        self._win.mouse_pos = [self._win.width / 2, self._win.height / 2]
        self.advance_frames(45)
        assert not wb_screen.left_enter
        assert wb_screen.left_x == 0

    def test_entering_right(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.pos = (0, 0)

        self._win.mouse_pos = [self._win.width * 0.98, self._win.height / 2]
        self.advance_frames(50)
        assert wb_screen.right_enter
        assert wb_screen.right_x == 0.75

        self._win.mouse_pos = [self._win.width / 2, self._win.height / 2]
        self.advance_frames(50)
        assert not wb_screen.right_enter
        assert wb_screen.right_x == 0.95
