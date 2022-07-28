import asyncio

from kivy.app import async_runTouchApp

from codejam.client.widgets.testcanvas import TestCanvas  # noqa: F401
from codejam.client.widgets.testcanvas import root_widget  # noqa: F401
from codejam.client.widgets.whiteboard import WhiteBoard  # noqa: F401
from codejam.client.widgets.whiteboardscreen import WhiteBoardScreen  # noqa: F401

if __name__ == "__main__":  # pragma: no cover

    async def run_app(root):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root, async_lib="asyncio")
        if root.ws:
            root.ws.cancel()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app(root_widget))
    loop.close()
