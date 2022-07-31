import uuid
from datetime import datetime, timedelta
from enum import Enum
from random import random
from typing import Callable, Dict, Tuple

from kivy.graphics import Color, Line, Rectangle
from kivy.input import MotionEvent
from kivy.properties import BoundedNumericProperty, ListProperty, StringProperty
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import DrawOperations, Topic, TopicEnum


class Tools(Enum):
    """Enum for all GUI tools to draw"""

    CIRCLE = "circle"
    LINE = "line"
    FRAME = "frame"
    RECT = "rect"


class DrawCanvas(Widget):
    """TestCanvas Widget"""

    colour = ListProperty([random(), 1, 1])
    line_width = BoundedNumericProperty(2, min=1, max=50, errorvalue=1)
    tool = StringProperty("line")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drawables: Dict[str, Callable[[MotionEvent], None]] = {
            Tools.FRAME.value: self._draw_frame,
            Tools.LINE.value: self._draw_line,
            Tools.RECT.value: self._draw_rectangle,
        }

        self.updates: Dict[
            str,
            Callable[[MotionEvent], Tuple[uuid.UUID, DrawOperations, LineData | RectData]],
        ] = {
            Tools.FRAME.value: self._update_frame,
            Tools.LINE.value: self._update_line,
            Tools.RECT.value: self._update_rectangle,
        }
        self.last_draw_time = None

    def on_touch_down(self, touch: MotionEvent) -> None:
        """Called when a touch down event occurs"""
        if self.screen.manager.can_draw:
            if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
                with self.canvas:
                    Color(*self.colour, mode="hsv")
                    self.drawables.get(self.tool)(touch)

    def select_operator(
        self, touch_data: Dict
    ) -> Callable[[MotionEvent], Tuple[uuid.UUID, DrawOperations, LineData | RectData]]:
        """Selects operation based on keys in touch.ud dictionary"""
        constraints = [x.value for x in Tools]
        checks = (key if key in touch_data else None for key in constraints)
        target_class = next((target for target in checks if target is not None), None)
        return self.updates.get(target_class)

    def on_touch_move(self, touch: MotionEvent) -> None:
        """Called when a touch move event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            operator = self.select_operator(touch.ud)
            if operator:
                draw_id, operation, data = operator(touch)
                if self.tool == Tools.LINE.value:
                    self.screen.message = self._prepare_message(
                        draw_id=draw_id, operation=operation, data=data
                    ).json(models_as_dict=True)

    def on_touch_up(self, touch: MotionEvent) -> None:
        """Called when a touch up event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            operator = self.select_operator(touch.ud)
            if operator:
                if self.tool != Tools.LINE.value:
                    draw_id, operation, data = operator(touch)
                    self.screen.message = self._prepare_message(
                        draw_id=draw_id, operation=operation, data=data
                    ).json(models_as_dict=True)

    def _draw_frame(self, touch: MotionEvent) -> None:
        """Draw a frame"""
        touch.ud[Tools.FRAME.value] = Line(points=(touch.x, touch.y), width=self.line_width)
        self.ids[uuid.uuid4()] = touch.ud[Tools.FRAME.value]

    def _update_frame(self, touch: MotionEvent) -> Tuple[uuid.UUID, DrawOperations, LineData]:
        """Update a frame"""
        with self.canvas:
            if not touch.ud.get("origin"):
                touch.ud["origin"] = (touch.x - self.offset_x, touch.y - self.offset_y)
            pos = touch.ud["origin"]
            (x, x2), (y, y2) = [
                sorted((pos[0], touch.x - self.offset_x)),
                sorted((pos[1], touch.y - self.offset_y)),
            ]
            touch.ud[Tools.FRAME.value].points = [x, y, x2, y, x2, y2, x, y2, x, y]
        return self._prepare_frame_data(touch=touch)

    def _draw_line(self, touch: MotionEvent) -> None:
        """Draw a line"""
        touch.ud[Tools.LINE.value] = Line(
            points=(touch.x - self.offset_x, touch.y - self.offset_y),
            width=self.line_width,
        )
        self.ids[uuid.uuid4()] = touch.ud[Tools.LINE.value]

    def _update_line(self, touch: MotionEvent) -> Tuple[uuid.UUID, DrawOperations, LineData]:
        """Update a line"""
        with self.canvas:
            if self.screen.snail_active:
                if (
                    not self.last_draw_time
                    or self.last_draw_time + timedelta(milliseconds=200) <= datetime.now()
                ):
                    self.last_draw_time = datetime.now()
                    touch.ud[Tools.LINE.value].points += (
                        touch.x - self.offset_x,
                        touch.y - self.offset_y,
                    )
            else:
                touch.ud[Tools.LINE.value].points += (
                    touch.x - self.offset_x,
                    touch.y - self.offset_y,
                )
        return self._prepare_line_data(touch=touch)

    def _draw_rectangle(self, touch: MotionEvent) -> None:
        """Draw a rectangle"""
        touch.ud[Tools.RECT.value] = Rectangle(
            pos=(touch.x - self.offset_x, touch.y - self.offset_y), size=(0, 0)
        )

    def _update_rectangle(self, touch: MotionEvent) -> Tuple[uuid.UUID, DrawOperations, RectData]:
        """Update rectangle"""
        if not touch.ud.get("origin"):
            touch.ud["origin"] = (touch.x, touch.y)
        pos = touch.ud["origin"]
        touch.ud[Tools.RECT.value].pos = [
            min(pos[0] - self.offset_x, touch.x - self.offset_x),
            min(pos[1] - self.offset_y, touch.y - self.offset_y),
        ]
        touch.ud[Tools.RECT.value].size = [
            abs(touch.x - self.offset_x - pos[0]),
            abs(touch.y - self.offset_y - pos[1]),
        ]
        return self._prepare_rectangle_data(touch=touch)

    def _prepare_frame_data(
        self, touch: MotionEvent
    ) -> Tuple[uuid.UUID, DrawOperations, LineData]:
        """Prepare data for line message."""
        draw_id = uuid.uuid4()
        operation = DrawOperations.FRAME
        data = LineData(
            line=touch.ud[Tools.FRAME.value].points,
            colour=self.colour,
            width=self.line_width,
        )
        self.ids[draw_id] = touch.ud[Tools.FRAME.value]
        return draw_id, operation, data

    def _prepare_line_data(self, touch: MotionEvent) -> Tuple[uuid.UUID, DrawOperations, LineData]:
        """Prepare data for line message."""
        draw_id = uuid.uuid4()
        operation = DrawOperations.LINE
        data = LineData(
            line=touch.ud[Tools.LINE.value].points,
            colour=self.colour,
            width=self.line_width,
        )
        self.ids[draw_id] = touch.ud[Tools.LINE.value]
        return draw_id, operation, data

    def _prepare_rectangle_data(
        self, touch: MotionEvent
    ) -> Tuple[uuid.UUID, DrawOperations, RectData]:
        """Prepare data for rectangle message."""
        draw_id = uuid.uuid4()
        operation = DrawOperations.RECT
        data = RectData(
            pos=touch.ud[Tools.RECT.value].pos,
            colour=self.colour,
            size=touch.ud[Tools.RECT.value].size,
        )
        self.ids[draw_id] = touch.ud[Tools.RECT.value]
        return draw_id, operation, data

    def _prepare_message(
        self, draw_id: uuid.UUID, operation: DrawOperations, data: LineData | RectData
    ) -> Message:
        """Prepare the draw message."""
        return Message(
            topic=Topic(type=TopicEnum.DRAW, operation=operation),
            username=self.screen.manager.username,
            game_id=self.screen.manager.game_id,
            value=PictureMessage(draw_id=str(draw_id), data=data),
        )
