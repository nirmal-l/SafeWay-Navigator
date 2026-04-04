from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps a guardian_token -> List of Observer WebSockets
        self.guardian_observers: Dict[str, List[WebSocket]] = {}
        
        # General active safety connections (for broadcasting Danger Pins)
        self.active_connections: List[WebSocket] = []

    async def connect_safety(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect_safety(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def connect_guardian(self, websocket: WebSocket, token: str):
        await websocket.accept()
        if token not in self.guardian_observers:
            self.guardian_observers[token] = []
        self.guardian_observers[token].append(websocket)

    def disconnect_guardian(self, websocket: WebSocket, token: str):
        if token in self.guardian_observers and websocket in self.guardian_observers[token]:
            self.guardian_observers[token].remove(websocket)
            if not self.guardian_observers[token]:
                del self.guardian_observers[token]

    async def broadcast_danger_pin(self, payload: dict):
        """Sends a newly dropped Danger Pin to all active users on the map."""
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "DANGER_PIN_UPDATE", "data": payload})
            except Exception:
                pass # Connection likely dropped

    async def broadcast_guardian_location(self, token: str, payload: dict):
        """Streams live GPS coordinate updates to any friend watching this specific token."""
        if token in self.guardian_observers:
            for connection in self.guardian_observers[token]:
                try:
                    await connection.send_json({"type": "GUARDIAN_LOCATION", "data": payload})
                except Exception:
                    pass

manager = ConnectionManager()
