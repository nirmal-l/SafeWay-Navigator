import { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = (import.meta.env.VITE_MAPBOX_TOKEN || '').trim().replace(/^['"]|['"]$/g, '');

export default function GuardianObserver({ token }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const marker = useRef(null);
  
  const [status, setStatus] = useState("Connecting to Tracker...");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    // 1. Initialize Map (only once)
    if (!map.current) {
      mapboxgl.accessToken = MAPBOX_TOKEN;
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [75.818981, 26.9124336], // Default Jaipur
        zoom: 12,
        pitch: 45
      });

      const el = document.createElement('div');
      el.className = 'guardian-marker';
      el.style.width = '24px';
      el.style.height = '24px';
      el.style.backgroundColor = 'var(--primary)';
      el.style.borderRadius = '50%';
      el.style.boxShadow = '0 0 20px var(--primary)';
      el.style.border = '3px solid white';
      el.style.transition = 'all 0.3s ease';

      marker.current = new mapboxgl.Marker(el)
        .setLngLat([75.818981, 26.9124336])
        .addTo(map.current);
    }

    // 2. Connect WebSocket via Vite proxy (/ws path proxied to port 8000)
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${window.location.host}/ws/guardian/${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setStatus("Connected. Waiting for GPS signal...");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "GUARDIAN_LOCATION") {
          const { lat, lng, timestamp } = msg.data;
          
          marker.current.setLngLat([lng, lat]);
          map.current.flyTo({ center: [lng, lat], zoom: 16 });
          
          setLastUpdate(timestamp);
          setStatus("Receiving Live GPS");
          setIsOffline(false);
        }
      } catch (err) {
        console.error("Parse error", err);
      }
    };

    ws.onclose = () => {
      setStatus("Connection Lost.");
      setIsOffline(true);
    };

    return () => {
      ws.close();
      if (map.current) map.current.remove();
    };
  }, [token]);

  // Check for inactivity
  useEffect(() => {
    if (!lastUpdate) return;
    const interval = setInterval(() => {
      const msSinceUpdate = new Date() - new Date(lastUpdate);
      if (msSinceUpdate > 15000) { // 15 seconds without GPS
        setIsOffline(true);
        setStatus("WARNING: GPS Signal Lost");
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      
      {/* HUD Panel */}
      <div style={{
        position: 'absolute', top: 20, left: 20,
        background: 'var(--bg-2)', padding: '20px', borderRadius: '12px',
        border: `1px solid ${isOffline ? 'var(--danger)' : 'var(--border-light)'}`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        zIndex: 10,
        minWidth: '250px'
      }}>
        <h2 style={{ margin: '0 0 10px', fontSize: '18px', color: 'white' }}>Live Route Guardian</h2>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <div className={isOffline ? "pulse-dot-danger" : "pulse-dot"} 
               style={{ backgroundColor: isOffline ? 'var(--danger)' : 'var(--safe-light)' }} />
          <span style={{ fontSize: '14px', color: isOffline ? 'var(--danger)' : 'var(--safe-light)', fontWeight: 'bold' }}>
            {status}
          </span>
        </div>

        {lastUpdate && (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Last seen: {new Date(lastUpdate).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
