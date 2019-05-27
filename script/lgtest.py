#!/usr/bin/env python3
"""Good persistent connection to WebOS TV"""

import asyncio
import websockets
import pprint
import logging

logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

printer = pprint.PrettyPrinter(indent=2)

result_handler = {}


class LGTVComponent:

    def __init__(self, uri):
        self._terminate = False
        self._uri = uri
        self._websocket = None

    async def reconnect(self):
        try:
            self._websocket = await websockets.connect(self._uri)
        except TimeoutError:
            return False
        return True

    async def ensure_connection(self, callback=None):
        if self._websocket is not None:
            return
        for i in range(0, 1):
            await asyncio.sleep(i)
            if self._terminate:
                return
            if await self.reconnect():
                if callback is not None:
                    asyncio.create_task(callback())
                return
#        self.state_offline()
        delay = 0
        while True:
            if delay < 10:
                delay += 1
            await asyncio.sleep(delay)
            if self._terminate:
                return
            if await self.reconnect():
                if callback is not None:
                    asyncio.create_task(callback())
                return

    async def message_loop(self):
        try:
#            self.register_listeners()
            async for message in self._websocket:
                printer.pprint(message)
        except Exception:
            if self._terminate:
                return
            self._websocket = None
            asyncio.create_task(self.ensure_connection(self.message_loop))

    async def ping(self):
        while True:
            if self._terminate:
                return
            if self._websocket is not None:
                poll = await self._websocket.ping()
                await poll
            await asyncio.sleep(1)

    async def connect(self):
        asyncio.create_task(self.ensure_connection(self.message_loop))
        asyncio.create_task(self.ping())

    def terminate(self):
        self._terminate = True
        if self._websocket is not None:
            asyncio.create_task(self._websocket.close())
            self._websocket = None

    def start(self):
        asyncio.get_event_loop().run_until_complete(
            self.connect())


tv = LGTVComponent("ws://192.168.2.113:3000")

tv.start()


async def stop():
    await asyncio.sleep(30)
    tv.terminate()


#asyncio.get_event_loop().run_until_complete(stop())
asyncio.get_event_loop().run_forever()
