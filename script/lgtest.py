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



class LGTVComponent:

    def __init__(self, uri):
        self._terminate = False
        self._uri = uri
        self._websocket = None
        self._msg_handler = {}

    async def reconnect(self):
        try:
            self._websocket = await websockets.connect(self._uri)
        except:
            return False
        return True

    async def ensure_connection(self, callback=None):
        if self._websocket is not None:
            return
        for i in range(0, 2):
            await asyncio.sleep(i)
            print("Try Online Reconnect")
            if self._terminate:
                return
            if await self.reconnect():
                if callback is not None:
                    asyncio.get_event_loop().create_task(callback())
                return
#        self.state_offline()
        delay = 0
        while True:
            print("Try Offline Reconnect with delay " + str(delay))
            if delay < 10:
                delay += 1
            await asyncio.sleep(delay)
            if self._terminate:
                return
            if await self.reconnect():
                asyncio.get_event_loop().create_task(self.message_loop())
                return

    async def message_loop(self):
        try:
            while True:
                message = await self._websocket.recv()
                printer.pprint(message)
        except:
            if self._terminate:
                return
            self._websocket = None
            asyncio.get_event_loop().create_task(self.ensure_connection())

    async def ping(self):
        while True:
            if self._terminate:
                return
            try:
                if self._websocket is not None:
                    async def pingpong():
                        pong = await self._websocket.ping()
                        await pong
                    await asyncio.wait_for(pingpong(), timeout=3)
            except:
                print("Ping timeout, reconnecting")
                asyncio.get_event_loop().create_task(self._websocket.close())
            await asyncio.sleep(1)

    async def connect(self):
        asyncio.get_event_loop().create_task(self.ensure_connection())
        asyncio.get_event_loop().create_task(self.ping())

    def terminate(self):
        self._terminate = True
        if self._websocket is not None:
            ws = self._websocket
            self._websocket = None
            asyncio.get_event_loop().create_task(ws.close())

    def start(self):
        asyncio.get_event_loop().run_until_complete(
            self.connect())


tv = LGTVComponent("ws://localhost:8080/ws")

tv.start()


async def stop():
    await asyncio.sleep(30)
    tv.terminate()


asyncio.get_event_loop().run_until_complete(stop())
asyncio.get_event_loop().run_forever()
