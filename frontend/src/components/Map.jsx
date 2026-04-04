import { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const JAIPUR_CENTER = [75.7873, 26.9124];

const PIN_COLORS = {
  broken_light: '#F59E0B',
  suspicious: '#EF4444',
  dog: '#A78BFA',
  footpath: '#64748B',
  other: '#94A3B8',
};
const PIN_EMOJIS = {
  broken_light: '💡',
  suspicious: '⚠️',
  dog: '🐕',
  footpath: '🚧',
  other: '📍',
};

function readToken() {
  const t = import.meta.env.VITE_MAPBOX_TOKEN ?? '';
  const clean = t.trim();
  if (!clean || clean === 'PASTE_YOUR_MAPBOX_TOKEN_HERE') return '';
  return clean;
}

export default function Map({ routes, activeRouteIndex, dangerPins, userLocation, onMapClick, isNavigating }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markersRef = useRef([]);
  const token = readToken();

  useEffect(() => {
    if (!token) return;
    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/navigation-night-v1',
      center: JAIPUR_CENTER,
      zoom: 13,
      pitch: 45,
      bearing: 0,
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), 'top-right');

    map.on('load', () => {
      setMapLoaded(true);

      map.addSource('safe-routes', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.addLayer({
        id: 'ffnn-alt-routes',
        type: 'line',
        source: 'safe-routes',
        filter: ['!=', ['get', 'isActive'], true],
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#475569',
          'line-width': 4,
          'line-opacity': 0.4,
          'line-dasharray': [2, 3],
        },
      });

      map.addLayer({
        id: 'ffnn-route-glow',
        type: 'line',
        source: 'safe-routes',
        filter: ['==', ['get', 'isActive'], true],
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#7C3AED',
          'line-width': 24,
          'line-opacity': 0.15,
          'line-blur': 14,
        },
      });

      map.addLayer({
        id: 'ffnn-safe-route',
        type: 'line',
        source: 'safe-routes',
        filter: ['==', ['get', 'isActive'], true],
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': [
            'match', ['get', 'traffic'],
            'heavy', '#EF4444',
            'moderate', '#FBBF24',
            'severe', '#991B1B',
            '#7C3AED'
          ],
          'line-width': 5,
          'line-opacity': 0.95,
        },
      });

      map.addSource('danger-pins', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });
    });

    // Wire map click → DangerPin modal
    map.on('click', (e) => {
      if (onMapClick) {
        onMapClick({ lat: e.lngLat.lat, lng: e.lngLat.lng });
      }
    });

    mapRef.current = map;
    return () => map.remove();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;
    const source = map.getSource('safe-routes');
    if (!source) return;

    if (routes && routes.length > 0) {
      const features = [];
      routes.forEach((rt, idx) => {
        const isActive = idx === activeRouteIndex;
        if (rt.congestion && rt.congestion.length > 0 && rt.coordinates.length > 1) {
          const cong = rt.congestion;
          for (let i = 0; i < rt.coordinates.length - 1; i++) {
            const state = cong[i] || 'low';
            features.push({
              type: 'Feature',
              properties: { isActive, traffic: state },
              geometry: { type: 'LineString', coordinates: [rt.coordinates[i], rt.coordinates[i + 1]] },
            });
          }
        } else {
          features.push({
            type: 'Feature',
            properties: { isActive, traffic: 'low' },
            geometry: { type: 'LineString', coordinates: rt.coordinates },
          });
        }
      });
      source.setData({ type: 'FeatureCollection', features });

      const activeRt = routes[activeRouteIndex];
      if (activeRt && activeRt.coordinates) {
        const lngs = activeRt.coordinates.map((c) => c[0]);
        const lats = activeRt.coordinates.map((c) => c[1]);
        map.fitBounds(
          [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
          { padding: 80, duration: 1200, pitch: 45 }
        );
      }
      if (map.getLayer('ffnn-alt-routes')) {
        map.setLayoutProperty('ffnn-alt-routes', 'visibility', isNavigating ? 'none' : 'visible');
      }
    } else {
      source.setData({ type: 'FeatureCollection', features: [] });
    }
  }, [routes, activeRouteIndex, mapLoaded, isNavigating]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    dangerPins.forEach((pin) => {
      const el = document.createElement('div');
      const color = PIN_COLORS[pin.category] || '#94A3B8';
      el.style.cssText = `
        width: 32px; height: 32px;
        background: ${color};
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        display: flex; align-items: center; justify-content: center;
        font-size: 14px;
        box-shadow: 0 4px 16px ${color}60;
        cursor: pointer;
        border: 2px solid rgba(255,255,255,0.25);
        transition: transform 200ms ease;
      `;
      const inner = document.createElement('span');
      inner.style.transform = 'rotate(45deg)';
      inner.textContent = PIN_EMOJIS[pin.category] || '📍';
      el.appendChild(inner);

      const marker = new mapboxgl.Marker({ element: el, anchor: 'bottom-left' })
        .setLngLat([pin.lng, pin.lat])
        .setPopup(
          new mapboxgl.Popup({ offset: 25, className: 'ffnn-popup' }).setHTML(
            `<div style="color:#F9FAFB;font-family:Inter,sans-serif;padding:10px;background:#111827;border-radius:12px">
              <strong style="text-transform:capitalize;font-size:13px">${pin.category.replace('_', ' ')}</strong>
              ${pin.description ? `<p style="font-size:12px;margin-top:5px;color:#9CA3AF">${pin.description}</p>` : ''}
              <p style="font-size:10px;color:#6B7280;margin-top:6px">⏱ Expires in 24h</p>
            </div>`
          )
        )
        .addTo(map);
      markersRef.current.push(marker);
    });
  }, [dangerPins, mapLoaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !userLocation) return;

    if (!mapContainer.current.userMarker) {
      const el = document.createElement('div');
      el.style.cssText = `
        width: 18px; height: 18px;
        background: #7C3AED;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 0 0 6px rgba(124,58,237,0.25), 0 2px 8px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      `;

      const pulseRing = document.createElement('div');
      pulseRing.className = 'nav-pulse-ring';
      pulseRing.style.cssText = `
        position: absolute; top: -10px; left: -10px; right: -10px; bottom: -10px;
        border-radius: 50%; border: 2px solid #A78BFA;
        animation: pinPulse 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
        display: none;
      `;
      el.appendChild(pulseRing);

      const marker = new mapboxgl.Marker({ element: el, pitchAlignment: 'map' })
        .setLngLat([userLocation.lng, userLocation.lat])
        .addTo(map);

      mapContainer.current.userMarker = marker;
      mapContainer.current.userMarkerEl = el;
      mapContainer.current.pulseRingEl = pulseRing;
    } else {
      mapContainer.current.userMarker.setLngLat([userLocation.lng, userLocation.lat]);
    }

    if (mapContainer.current.pulseRingEl) {
      mapContainer.current.pulseRingEl.style.display = isNavigating ? 'block' : 'none';
      mapContainer.current.userMarkerEl.style.boxShadow = isNavigating
        ? '0 0 0 8px rgba(124,58,237,0.35)' : '0 0 0 6px rgba(124,58,237,0.25), 0 2px 8px rgba(0,0,0,0.3)';
    }

    if (isNavigating) {
      map.flyTo({
        center: [userLocation.lng, userLocation.lat],
        zoom: Math.max(map.getZoom(), 16),
        speed: 0.8, curve: 1,
        easing(t) { return t; }
      });
    }

    if (!document.getElementById('ffnn-marker-styles')) {
      const style = document.createElement('style');
      style.id = 'ffnn-marker-styles';
      style.innerHTML = `
        @keyframes pinPulse {
          0% { transform: scale(0.5); opacity: 0; }
          50% { opacity: 0.8; }
          100% { transform: scale(1.8); opacity: 0; }
        }
        .mapboxgl-popup-content {
          background: #111827 !important;
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 14px !important;
          padding: 0 !important;
          box-shadow: 0 12px 40px rgba(0,0,0,0.6) !important;
        }
        .mapboxgl-popup-tip {
          border-top-color: #111827 !important;
        }
        .mapboxgl-popup-close-button {
          color: #9CA3AF !important;
          font-size: 16px !important;
          padding: 4px 8px !important;
        }
      `;
      document.head.appendChild(style);
    }
  }, [userLocation, mapLoaded, isNavigating]);

  if (!token) {
    return (
      <div style={{
        width: '100%', height: '100%',
        background: 'radial-gradient(ellipse at 30% 40%, rgba(124,58,237,0.08) 0%, var(--bg-0) 50%, var(--bg-0) 100%)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: '28px',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', width: '500px', height: '500px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%)',
          filter: 'blur(80px)', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          animation: 'float-slow 20s ease-in-out infinite',
        }} />

        <div style={{
          width: '96px', height: '96px', borderRadius: '32px',
          background: 'linear-gradient(135deg, var(--primary), #4338CA, var(--accent))',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '44px',
          boxShadow: '0 20px 80px var(--primary-glow)',
          position: 'relative', zIndex: 1,
          border: '1px solid rgba(255,255,255,0.1)',
          animation: 'splash-icon-in 0.8s var(--ease-spring) both',
        }}>🗺️</div>

        <div style={{ textAlign: 'center', maxWidth: '360px', position: 'relative', zIndex: 1 }}>
          <h2 className="gradient-text" style={{
            fontSize: '24px', fontWeight: '800', marginBottom: '14px', letterSpacing: '-0.03em',
            fontFamily: 'Space Grotesk, sans-serif',
          }}>
            Mapbox Token Required
          </h2>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.7' }}>
            Add your free Mapbox token to <code style={{ color: 'var(--text-accent)', background: 'var(--primary-surface)', padding: '2px 8px', borderRadius: '5px', fontSize: '13px', border: '1px solid rgba(124,58,237,0.2)' }}>.env</code> to enable the map.
          </p>
        </div>

        <div style={{
          background: 'var(--primary-surface)', border: '1px solid rgba(124,58,237,0.2)',
          borderRadius: '14px', padding: '18px 32px',
          color: 'var(--text-accent)', fontSize: '13px', fontFamily: 'JetBrains Mono, monospace',
          position: 'relative', zIndex: 1,
          boxShadow: '0 8px 32px rgba(124,58,237,0.1)',
        }}>
          VITE_MAPBOX_TOKEN=pk.ey...
        </div>
      </div>
    );
  }

  return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />;
}
