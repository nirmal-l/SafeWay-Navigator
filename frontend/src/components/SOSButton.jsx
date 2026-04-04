import { useState, useRef } from 'react';

const FAKE_CALL_SCRIPT = [
  "Hey! Are you almost here? I can see you on the map.",
  "Take the main road, it's better lit.",
  "I'll wait for you at the gate. Stay on the phone.",
];

export default function SOSButton({ guardianToken, onShareGuardian }) {
  const [callActive, setCallActive] = useState(false);
  const [callLine, setCallLine] = useState(0);
  const [showSOS, setShowSOS] = useState(false);
  const intervalRef = useRef(null);

  const startFakeCall = () => {
    setCallActive(true);
    setCallLine(0);
    setShowSOS(false);
    let line = 0;
    intervalRef.current = setInterval(() => {
      line += 1;
      if (line >= FAKE_CALL_SCRIPT.length) {
        clearInterval(intervalRef.current);
        setCallLine(FAKE_CALL_SCRIPT.length - 1);
      } else {
        setCallLine(line);
      }
    }, 4000);
  };

  const endFakeCall = () => {
    setCallActive(false);
    clearInterval(intervalRef.current);
  };

  const copyGuardianLink = () => {
    if (guardianToken) {
      const link = `${window.location.origin}/guardian/${guardianToken}`;
      navigator.clipboard.writeText(link).catch(() => {});
      onShareGuardian && onShareGuardian(link);
    }
    setShowSOS(false);
  };

  // ── Fake Call UI ──
  if (callActive) {
    return (
      <div className="modal-overlay" style={{ alignItems: 'flex-end', paddingBottom: '100px' }}>
        <div className="glass-card modal-content" style={{
          padding: '32px', textAlign: 'center', minWidth: '300px', maxWidth: '360px',
          border: '1px solid rgba(16,185,129,0.2)',
          background: 'linear-gradient(180deg, rgba(16,185,129,0.04), var(--glass-bg))',
        }}>
          {/* Animated phone ring */}
          <div style={{
            width: '64px', height: '64px', borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--safe), #059669)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px', fontSize: '28px',
            boxShadow: '0 0 40px var(--safe-glow)',
            animation: 'sos-pulse 2s infinite',
            position: 'relative', zIndex: 1,
          }}>📞</div>

          <div style={{ fontSize: '10px', fontWeight: '700', color: 'var(--safe)', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '8px', position: 'relative', zIndex: 1 }}>
            Incoming Call
          </div>
          <div style={{ fontSize: '20px', fontWeight: '800', marginBottom: '8px', letterSpacing: '-0.02em', position: 'relative', zIndex: 1, fontFamily: 'Space Grotesk, sans-serif' }}>Priya (Guardian)</div>
          <div style={{
            fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '24px',
            minHeight: '40px', fontStyle: 'italic',
            padding: '14px 18px', background: 'var(--bg-2)', borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--glass-border)', position: 'relative', zIndex: 1,
          }}>
            &ldquo;{FAKE_CALL_SCRIPT[callLine]}&rdquo;
          </div>

          <button id="end-fake-call-btn" className="btn btn-danger"
            style={{ borderRadius: 'var(--radius-full)', padding: '13px 36px', fontSize: '14px', position: 'relative', zIndex: 1 }}
            onClick={endFakeCall}
          >
            📵 End Call
          </button>
        </div>
      </div>
    );
  }

  // ── Main SOS Button ──
  return (
    <>
      {/* Decorative outer ring */}
      <div className="sos-ring" />

      {/* Main SOS Button */}
      <button
        id="sos-main-btn"
        className={`sos-btn ${showSOS ? 'active' : ''}`}
        onClick={() => setShowSOS(!showSOS)}
      >🆘</button>

      {/* SOS Options Panel */}
      {showSOS && (
        <div className="glass-card animate-scale-in" style={{
          position: 'absolute', bottom: '100px', right: '24px',
          padding: '20px', zIndex: 200, width: '240px',
          border: '1px solid rgba(239,68,68,0.15)',
          background: 'linear-gradient(180deg, rgba(239,68,68,0.03), var(--glass-bg))',
        }}>
          <div style={{
            fontSize: '10px', fontWeight: '700', color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '14px',
            display: 'flex', alignItems: 'center', gap: '6px',
            position: 'relative', zIndex: 1,
          }}>
            <span style={{ color: 'var(--danger)', animation: 'breathe 2s ease-in-out infinite' }}>●</span> Safety Options
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative', zIndex: 1 }}>
            <button id="fake-call-btn" className="btn btn-primary"
              style={{ justifyContent: 'flex-start', gap: '10px', padding: '12px 16px', fontSize: '13px' }}
              onClick={startFakeCall}
            >
              <span>📞</span><span>Fake Phone Call</span>
            </button>
            <button id="guardian-share-btn" className="btn btn-ghost"
              style={{ justifyContent: 'flex-start', gap: '10px', padding: '12px 16px', fontSize: '13px' }}
              onClick={copyGuardianLink}
              disabled={!guardianToken}
            >
              <span>🔗</span><span>Share Guardian Link</span>
            </button>
            <button id="emergency-call-btn" className="btn btn-danger"
              style={{ justifyContent: 'flex-start', gap: '10px', padding: '12px 16px', fontSize: '13px' }}
              onClick={() => { window.location.href = 'tel:112'; }}
            >
              <span>🚨</span><span>Call Emergency (112)</span>
            </button>

            <div style={{ height: '1px', background: 'var(--glass-border)', margin: '4px 0' }} />

            <button onClick={() => setShowSOS(false)}
              style={{
                background: 'none', border: 'none', color: 'var(--text-muted)',
                cursor: 'pointer', fontSize: '12px', padding: '6px', fontFamily: 'Inter, sans-serif',
                fontWeight: '500', transition: 'color 150ms ease',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
            >Cancel</button>
          </div>
        </div>
      )}
    </>
  );
}
