

export default function SafetyHUD({ route, dangerPins }) {
  if (!route) return null;

  const score = route.safety_score;
  const scoreColor = score >= 70 ? 'var(--safe)' : score >= 40 ? 'var(--warn)' : 'var(--danger)';

  const activePins = dangerPins?.filter(p => !p.resolved) || [];
  const radiusDegrees = 0.01;
  const pinsOnRoute = activePins.filter(p => {
    return route.coordinates.some(coord => {
      // coord is [lng, lat] (GeoJSON/Mapbox format)
      const dLng = Math.abs(coord[0] - p.lng);
      const dLat = Math.abs(coord[1] - p.lat);
      return dLat < radiusDegrees && dLng < radiusDegrees;
    });
  }).length;

  return (
    <div className="clean-card animate-slide-up" style={{
      position: 'absolute', bottom: '20px', left: '20px', width: '380px',
      padding: 0, zIndex: 100, overflow: 'hidden'
    }}>
      <div style={{
        padding: '20px', borderBottom: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center', gap: '20px',
      }}>
        {/* Score Ring */}
        <div className="score-circle" style={{ width: '80px', height: '80px', flexShrink: 0 }}>
          <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--bg-2)" strokeWidth="6" />
            <circle cx="50" cy="50" r="45" fill="none" stroke={scoreColor} strokeWidth="6"
              strokeDasharray={`${(score / 100) * 283} 283`}
              strokeLinecap="round" style={{ transition: 'stroke-dasharray 1s ease-out' }} />
          </svg>
          <div className="score-text">
            <div className="score-number" style={{ color: scoreColor }}>{score}</div>
          </div>
        </div>

        <div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
            {score >= 70 ? 'Safe Route' : score >= 40 ? 'Moderate Risk' : 'High Risk'}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
             This route avoids high-risk areas and maximizes street lighting.
          </div>
        </div>
      </div>

      <div style={{ padding: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div className="stat-card">
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>💡</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>{Math.round((route.lit_segments / Math.max(1, (route.distance_m/100))) * 100)}%</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Well Lit</div>
        </div>
        <div className="stat-card" style={{ borderColor: pinsOnRoute > 0 ? 'var(--danger)' : 'var(--border-light)' }}>
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>⚠️</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: pinsOnRoute > 0 ? 'var(--danger)' : 'var(--text-primary)' }}>{pinsOnRoute}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Hazards Nearby</div>
        </div>
        <div className="stat-card">
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>🏛️</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>{route.safe_haven_count}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Safe Havens</div>
        </div>
        <div className="stat-card">
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>🚇</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>{route.transit_nearby > 0 ? 'Yes' : 'No'}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Transit Access</div>
        </div>
      </div>
    </div>
  );
}
