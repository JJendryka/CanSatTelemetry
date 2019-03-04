import websockets
import asyncio
from threading import Thread


class Server(Thread):
    def __init__(self, packet_queue):
        Thread.__init__(self)
        self.packet_queue = packet_queue
        self.connected = set()
        self.loop = []

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handler, 'localhost', 25565)
        self.loop.run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print("User connected!")
        while True:
            await asyncio.sleep(1)

    def broadcast(self, message):
        future = asyncio.run_coroutine_threadsafe(
            self.send_to_all(message), self.loop)
        _ = future.result()

    async def send_to_all(self, message):
        to_remove = set()
        for client in self.connected:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                to_remove.add(client)
        for client in to_remove:
            self.connected.remove(client)
