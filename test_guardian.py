import asyncio
import json
import websockets

async def simulate_walk():
    uri = "ws://localhost:8000/ws/safety"
    token = "GHOST_TOKEN"
    
    path = [
        [26.9064, 75.8074],
        [26.9070, 75.8080],
        [26.9080, 75.8090],
        [26.9090, 75.8100]
    ]

    async with websockets.connect(uri) as ws:
        print(f"Connected to {uri}. Broadcasting Infinity Loop for token: {token}")
        while True:
            for lat, lng in path:
                try:
                    await ws.send(json.dumps({
                        "type": "LIVE_LOCATION",
                        "token": token,
                        "lat": lat,
                        "lng": lng,
                        "timestamp": "2026-04-03T10:00:00Z"
                    }))
                    print(f"Sent coord: {lat}, {lng}")
                    await asyncio.sleep(2)
                except Exception as e:
                    print("Simulation socket error", e)
                    break

if __name__ == "__main__":
    asyncio.run(simulate_walk())
