export default function LoadingScreen({ statusMessage }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'var(--bg-0)', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', color: 'var(--text-primary)',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{
        width: '56px', height: '56px', borderRadius: '16px',
        background: 'var(--bg-1)', border: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '24px', marginBottom: '24px', boxShadow: 'var(--shadow-md)'
      }}>
        🛡️
      </div>
      
      <h1 style={{ fontSize: '24px', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
        Night Navigator
      </h1>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
        <div className="spinner" style={{ width: '12px', height: '12px' }} />
        <span style={{ fontSize: '13px', fontWeight: '500' }}>{statusMessage || 'Initializing Environment...'}</span>
      </div>
      
      <div style={{
        position: 'absolute', bottom: '40px', fontSize: '11px', color: 'var(--border-hover)',
        letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: '600'
      }}>
        Offline-Ready Architecture
      </div>
    </div>
  );
}
