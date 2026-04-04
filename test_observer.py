import asyncio
import websockets
import sys

async def view_stream():
    uri = "ws://localhost:8000/ws/guardian/GHOST_TOKEN"
    print(f"Attempting to connect to {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("Successfully connected! Waiting for data...")
            while True:
                msg = await ws.recv()
                print("Received:", msg)
    except Exception as e:
        print("Failed to connect or connection dropped:", str(e))

if __name__ == "__main__":
    asyncio.run(view_stream())
