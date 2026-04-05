import { useState, useEffect } from 'react';

// NOTE: "Nearby Users" & "Conditions" are simulated for hackathon demo purposes.
// In production, these would pull from real WebSocket connection counts & weather APIs.
export default function DashboardStats() {
  const [time, setTime] = useState(new Date());
  const [users, setUsers] = useState(342);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    const userTimer = setInterval(() => setUsers(prev => prev + (Math.random() > 0.5 ? 1 : -1)), 3500);
    return () => { clearInterval(timer); clearInterval(userTimer); };
  }, []);

  return (
    <div className="clean-card animate-slide-up hover-scale" style={{
      position: 'absolute', top: '20px', right: '70px', width: '280px',
      padding: '16px', zIndex: 100
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--safe)' }} />
          <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)' }}>System Status</span>
        </div>
        <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: 'var(--text-muted)' }}>
          {time.toLocaleTimeString('en-US', { hour12: false })}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div style={{ background: 'var(--bg-2)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>Nearby Users</div>
          <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>{users}</div>
        </div>
        <div style={{ background: 'var(--bg-2)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>Safety Index</div>
          <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--safe)' }}>High</div>
        </div>
      </div>
      
      <div style={{ marginTop: '12px', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Conditions</span>
          <span style={{ fontSize: '12px' }}>🌙 Clear</span>
        </div>
        <div style={{ height: '4px', background: 'var(--bg-3)', borderRadius: '2px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: '85%', background: 'var(--primary)' }} />
        </div>
        <div style={{ textAlign: 'right', marginTop: '4px', fontSize: '10px', color: 'var(--text-muted)' }}>
          85% Visibility
        </div>
      </div>
    </div>
  );
}
