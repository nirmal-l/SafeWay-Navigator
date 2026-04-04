import { useState, useRef } from 'react';

const JAIPUR_BBOX = "75.60,26.68,76.00,27.12";
const JAIPUR_PROXIMITY = "75.7873,26.9124";

const PRESETS = [
  { label: 'Hawa Mahal', icon: '🏛️', coords: [75.8267, 26.9239] },
  { label: 'Raja Park', icon: '🏘️', coords: [75.8288, 26.8967] },
  { label: 'MI Road', icon: '🛣️', coords: [75.8040, 26.9155] },
  { label: 'JLN Marg', icon: '📍', coords: [75.8153, 26.8631] },
];

const VEHICLES = [
  { id: 'drive', icon: '🚗', label: 'Car' },
  { id: 'bike', icon: '🏍️', label: 'Bike' },
  { id: 'walk', icon: '🚶', label: 'Walk' },
];

export default function SearchPanel({ onRouteRequest, loading, routes, activeRouteIndex, onSelectRoute, onClear, isNavigating, setIsNavigating, userLocation }) {
  const [startQuery, setStartQuery] = useState('');
  const [endQuery, setEndQuery] = useState('');
  const [startCoords, setStartCoords] = useState(null);
  const [endCoords, setEndCoords] = useState(null);
  const [activeInput, setActiveInput] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  const [vehicleType, setVehicleType] = useState('walk');
  const timeoutRef = useRef(null);

  const fetchGeocode = async (query) => {
    if (!query || query.length < 3) { setSuggestions([]); return; }

    try {
      const token = import.meta.env.VITE_MAPBOX_TOKEN?.trim();
      const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?proximity=${JAIPUR_PROXIMITY}&bbox=${JAIPUR_BBOX}&access_token=${token}`;
      const res = await fetch(url);
      const data = await res.json();
      setSuggestions(data.features || []);
    } catch (e) { console.error(e); }
    finally { /* done */ }
  };

  const handleQueryChange = (val, type) => {
    if (type === 'start') { setStartQuery(val); setStartCoords(null); }
    else { setEndQuery(val); setEndCoords(null); }
    setActiveInput(type);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => fetchGeocode(val), 400);
  };

  const selectPlace = (feature) => {
    const coords = feature.center;
    if (activeInput === 'start') { setStartQuery(feature.place_name); setStartCoords([coords[1], coords[0]]); }
    else { setEndQuery(feature.place_name); setEndCoords([coords[1], coords[0]]); }
    setSuggestions([]);
    setActiveInput(null);
  };

  const handlePresetClick = (preset) => {
    if (activeInput === 'start' || !startCoords) {
      setStartQuery(preset.label);
      setStartCoords([preset.coords[1], preset.coords[0]]);
      setActiveInput('end');
    } else {
      setEndQuery(preset.label);
      setEndCoords([preset.coords[1], preset.coords[0]]);
      setActiveInput(null);
    }
  };

  const handleCalculate = () => {
    if (startCoords && endCoords) {
      onRouteRequest(startCoords, endCoords, vehicleType);
      setActiveInput(null);
      setSuggestions([]);
    }
  };

  const handleClear = () => {
    setStartQuery(''); setEndQuery('');
    setStartCoords(null); setEndCoords(null);
    setActiveInput('start');
    onClear();
  };

  const canCalculate = startCoords && endCoords && !loading;

  if (isNavigating) return null;

  /* ────────────────────────────────────────────────────────────
     ROUTE RESULTS VIEW
     ──────────────────────────────────────────────────────────── */
  if (routes && routes.length > 0) {
    return (
      <div className="clean-card animate-slide-up" style={{
        position: 'absolute', top: '20px', left: '20px', width: '380px',
        padding: 0, zIndex: 100, maxHeight: '88vh', overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px',
              background: 'var(--primary-surface)', color: 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
            }}>✓</div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>Safe Routes</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                {routes.length} options found
              </div>
            </div>
          </div>
          <button className="btn btn-ghost" onClick={handleClear} style={{ padding: '6px 12px', fontSize: '12px' }}>
            Clear
          </button>
        </div>

        {/* Route Cards */}
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {routes.map((rt, idx) => {
            const sf = rt.safety_score;
            const isActive = idx === activeRouteIndex;
            const scoreColor = sf >= 70 ? 'var(--safe)' : sf >= 40 ? 'var(--warn)' : 'var(--danger)';

            return (
              <div key={idx} onClick={() => onSelectRoute(idx)}
                className={`route-card ${isActive ? 'active' : ''} animate-slide-up delay-${idx + 1}`}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '42px', height: '42px', borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-1)', border: `2px solid ${scoreColor}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <span style={{ fontSize: '16px', fontWeight: '700', color: scoreColor }}>{sf}</span>
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {sf >= 70 ? 'Safe Route' : sf >= 40 ? 'Moderate Risk' : 'High Risk'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        Score {sf}/100
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>
                      {rt.distance_m >= 1000 ? `${(rt.distance_m / 1000).toFixed(1)} km` : `${rt.distance_m} m`}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {rt.duration_min} min
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <span className="chip chip-safe">💡 {rt.lit_segments} lit</span>
                  {rt.safe_haven_count > 0 && <span className="chip chip-blue">🏛️ {rt.safe_haven_count}</span>}
                  {rt.cctv_segments > 0 && <span className="chip">📹 {rt.cctv_segments}</span>}
                  {rt.transit_nearby > 0 && <span className="chip">🚌 {rt.transit_nearby}</span>}
                </div>

                {isActive && (
                  <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); setIsNavigating(true); }}
                    style={{ width: '100%', marginTop: '16px', padding: '12px' }}>
                    Start Journey
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  /* ────────────────────────────────────────────────────────────
     SEARCH VIEW
     ──────────────────────────────────────────────────────────── */
  return (
    <div className="clean-card animate-slide-up" style={{
      position: 'absolute', top: '20px', left: '20px', width: '380px',
      padding: 0, zIndex: 100, maxHeight: '90vh', overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid var(--border-light)',
      }}>
        <h1 style={{
          fontSize: '20px', fontWeight: '700', color: 'var(--text-primary)',
          letterSpacing: '-0.02em', margin: 0,
        }}>Night Navigator</h1>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Safe Routing for Jaipur
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        {/* Route Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
            <div style={{ position: 'relative' }}>
              <input className="input" placeholder="Start location"
                value={startQuery}
                onChange={(e) => handleQueryChange(e.target.value, 'start')}
                onClick={() => { setActiveInput('start'); fetchGeocode(startQuery); }}
              />
              <div style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', display: 'flex', gap: '4px' }}>
                <button className="btn btn-ghost" onClick={(e) => { e.preventDefault(); if (userLocation) { setStartQuery('Current Location'); setStartCoords([userLocation.lat, userLocation.lng]); }}}
                  style={{ padding: '4px 8px', fontSize: '11px', border: 'none' }}>
                  Locate
                </button>
              </div>
            </div>
            <div style={{ position: 'relative' }}>
              <input className="input" placeholder="Destination"
                value={endQuery}
                onChange={(e) => handleQueryChange(e.target.value, 'end')}
                onClick={() => { setActiveInput('end'); fetchGeocode(endQuery); }}
              />
            </div>
        </div>

        {/* Autocomplete */}
        {activeInput && suggestions.length > 0 && (
          <div className="clean-card animate-slide-up" style={{
            marginBottom: '20px', overflow: 'hidden', padding: 0
          }}>
            {suggestions.map((s, i) => (
              <div key={i} onClick={() => selectPlace(s)}
                style={{
                  padding: '12px 14px', cursor: 'pointer',
                  borderBottom: i < suggestions.length - 1 ? '1px solid var(--border-light)' : 'none',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-3)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)' }}>{s.text}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{s.place_name}</div>
              </div>
            ))}
          </div>
        )}

        {/* Quick Presets */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>Quick Destinations</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {PRESETS.map((p) => (
              <button key={p.label} className="btn btn-ghost" onClick={() => handlePresetClick(p)}
                style={{ padding: '6px 12px', fontSize: '12px', fontWeight: '500' }}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Vehicle Selector */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>Travel Mode</div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {VEHICLES.map(v => {
              const isSelected = vehicleType === v.id;
              return (
                <button key={v.id} onClick={() => setVehicleType(v.id)}
                  style={{
                    flex: 1, padding: '12px 8px',
                    background: isSelected ? 'var(--bg-3)' : 'var(--bg-2)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-primary)',
                    border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-light)'}`,
                    borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  <span style={{ fontSize: '18px' }}>{v.icon}</span>
                  <span style={{ fontSize: '12px', fontWeight: '500' }}>{v.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* CTA */}
        <button className="btn btn-primary"
          onClick={handleCalculate} disabled={!canCalculate}
          style={{ width: '100%', padding: '14px', fontSize: '14px', fontWeight: '600' }}
        >
          {loading ? 'Finding Route...' : 'Calculate Safe Route'}
        </button>
      </div>
    </div>
  );
}
