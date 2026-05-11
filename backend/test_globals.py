import asyncio

sim = {"count": 1}

async def ws_loop():
    while True:
        print(sim["count"])
        await asyncio.sleep(1)

async def updater():
    await asyncio.sleep(2.5)
    global sim
    sim = {"count": 999}
    print("UPDATED GLOBAL SIM")

async def main():
    task1 = asyncio.create_task(ws_loop())
    task2 = asyncio.create_task(updater())
    await asyncio.sleep(5)
    task1.cancel()

asyncio.run(main())
