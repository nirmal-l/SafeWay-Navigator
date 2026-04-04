import { useState } from 'react';

export default function GuardianLink({ token, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!token) return null;

  const link = `${window.location.origin}/guardian/${token}`;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
    }
  };

  const shareLink = async () => {
    if (navigator.share) {
      await navigator.share({
        title: 'Track my safe walk home',
        text: 'I\'m walking home. Track me live:',
        url: link,
      });
    } else {
      copyLink();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content" style={{
        width: '100%', maxWidth: '400px', padding: '32px',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '26px', position: 'relative', zIndex: 1 }}>
          <div style={{
            width: '68px', height: '68px', borderRadius: '22px',
            background: 'linear-gradient(135deg, var(--primary), #4338CA)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 18px', fontSize: '30px',
            boxShadow: '0 12px 40px var(--primary-glow)',
            border: '1px solid rgba(255,255,255,0.08)',
          }}>🔗</div>
          <h2 className="gradient-text" style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.02em', margin: '0 0 8px', fontFamily: 'Space Grotesk, sans-serif' }}>Guardian Link Ready</h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', margin: 0, maxWidth: '280px', marginInline: 'auto' }}>
            Share this link with a trusted person. They can watch your live location.
          </p>
        </div>

        {/* Link Box */}
        <div style={{
          background: 'var(--bg-2)', border: '1px solid var(--glass-border)',
          borderRadius: 'var(--radius-sm)', padding: '14px 16px', marginBottom: '14px',
          fontSize: '12px', color: 'var(--text-accent)',
          wordBreak: 'break-all', fontFamily: 'JetBrains Mono, monospace', lineHeight: '1.6',
          position: 'relative', zIndex: 1,
          transition: 'border-color 200ms ease',
        }}
          onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--glass-border-hover)'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--glass-border)'}
        >{link}</div>

        {/* Live status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          marginBottom: '22px', padding: '14px 16px',
          background: 'var(--safe-surface)', borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(16,185,129,0.15)',
          position: 'relative', zIndex: 1,
        }}>
          <div className="pulse-dot" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--safe-light)' }}>Live Tracking Active</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>Link expires in 4 hours</div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative', zIndex: 1 }}>
          <button id="copy-guardian-link-btn" className={`btn ${copied ? 'btn-safe' : 'btn-primary'}`}
            style={{ width: '100%', justifyContent: 'center', transition: 'all 300ms ease' }}
            onClick={copyLink}
          >
            {copied ? '✅ Copied to clipboard!' : '📋 Copy Link'}
          </button>
          <button id="share-guardian-link-btn" className="btn btn-ghost"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={shareLink}
          >📤 Share via WhatsApp / SMS</button>
          <button className="btn btn-ghost"
            style={{ width: '100%', justifyContent: 'center', fontSize: '13px', color: 'var(--text-muted)' }}
            onClick={onClose}
          >Close</button>
        </div>
      </div>
    </div>
  );
}
