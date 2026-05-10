import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws', max_size=10_000_000) as ws:
        msg1 = await ws.recv()
        data = json.loads(msg1)
        print("First msg positions count:", len(data.get('positions', [])))
        if len(data.get('positions', [])) > 0:
            print("First item:", data['positions'][0])

asyncio.run(test())
