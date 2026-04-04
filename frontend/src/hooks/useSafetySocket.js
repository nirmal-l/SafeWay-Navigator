import { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket URL uses Vite's /ws proxy (configured in vite.config.js → server.proxy)
// This routes ws://localhost:5173/ws/* → ws://localhost:8000/ws/*
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/safety`;

export function useSafetySocket(onDangerPinReceived) {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    let destroyed = false;
    let reconnectTimer = null;

    function connect() {
      if (destroyed) return;
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log("Connected to Safety Mesh");
      };

      ws.current.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'DANGER_PIN_UPDATE' && onDangerPinReceived) {
            onDangerPinReceived();
          }
        } catch (e) {
          console.error("Socket message error", e);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        if (!destroyed) {
          reconnectTimer = setTimeout(connect, 3000); // Auto reconnect
        }
      };
    }

    connect();

    return () => {
      destroyed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on intentional close
        ws.current.close();
      }
    };
  }, [onDangerPinReceived]);


  const sendLocation = useCallback((lat, lng, token) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'LIVE_LOCATION',
        token,
        lat,
        lng,
        timestamp: new Date().toISOString()
      }));
    }
  }, []);

  return { isConnected, sendLocation };
}
