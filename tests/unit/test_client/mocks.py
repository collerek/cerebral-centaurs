import asyncio


class WebsocketMock:
    def __init__(self):
        self.sleep = False
        self.refuse_connection = False
        self.cancel = False
        self.messages = []
        self.url = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return self

    def connect(self, url: str):
        if self.refuse_connection:
            raise ConnectionRefusedError()
        self.url = url
        return self

    async def send(self, value: str):
        self.messages.append(value)

    async def recv(self):
        if self.cancel:
            raise asyncio.CancelledError
        if self.sleep:
            self.sleep = False
            raise asyncio.exceptions.TimeoutError
        return self.messages.pop()
