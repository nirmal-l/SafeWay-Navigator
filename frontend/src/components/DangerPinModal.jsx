import { useState } from 'react';

const CATEGORIES = [
  { id: 'broken_light', label: 'Broken Streetlight', emoji: '💡', color: '#F59E0B', bg: 'rgba(245,158,11,0.08)' },
  { id: 'suspicious', label: 'Suspicious Activity', emoji: '⚠️', color: '#EF4444', bg: 'rgba(239,68,68,0.08)' },
  { id: 'dog', label: 'Aggressive Dog', emoji: '🐕', color: '#A78BFA', bg: 'rgba(139,92,246,0.08)' },
  { id: 'footpath', label: 'Unsafe Footpath', emoji: '🚧', color: '#64748B', bg: 'rgba(100,116,139,0.08)' },
  { id: 'other', label: 'Other', emoji: '📍', color: '#94A3B8', bg: 'rgba(148,163,184,0.08)' },
];

export default function DangerPinModal({ location, onSubmit, onClose }) {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedCategory) return;
    setSubmitting(true);
    await onSubmit(location.lat, location.lng, selectedCategory, description);
    setSubmitting(false);
    onClose();
  };

  return (
    <div className="modal-overlay bottom-sheet">
      <div className="glass-card modal-content" style={{
        width: '100%', maxWidth: '420px', padding: '24px',
        borderBottom: 'none', borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
      }}>
        {/* Handle bar */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '18px', position: 'relative', zIndex: 1 }}>
          <div style={{ width: '36px', height: '4px', borderRadius: '4px', background: 'var(--bg-4)' }} />
        </div>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', position: 'relative', zIndex: 1 }}>
          <div>
            <h2 className="gradient-text" style={{ fontSize: '18px', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>Report Safety Issue</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '5px', fontFamily: 'JetBrains Mono, monospace', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--danger)', fontSize: '8px' }}>●</span>
              {location.lat.toFixed(5)}, {location.lng.toFixed(5)}
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'var(--bg-3)', border: '1px solid var(--glass-border)',
            color: 'var(--text-muted)', fontSize: '16px', cursor: 'pointer',
            width: '34px', height: '34px', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 200ms ease',
          }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--glass-border-hover)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
          >✕</button>
        </div>

        {/* Category Grid */}
        <div style={{ marginBottom: '16px', position: 'relative', zIndex: 1 }}>
          <div className="section-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--accent)', fontSize: '10px' }}>◆</span>
            Issue Type
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            {CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat.id;
              return (
                <button key={cat.id} id={`danger-pin-${cat.id}`}
                  className={`category-btn ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedCategory(cat.id)}
                  style={{
                    background: isSelected ? cat.bg : undefined,
                    borderColor: isSelected ? cat.color : undefined,
                    color: isSelected ? cat.color : undefined,
                    boxShadow: isSelected ? `0 0 20px ${cat.color}20` : undefined,
                  }}
                >
                  <span style={{ fontSize: '18px' }}>{cat.emoji}</span>
                  <span style={{ lineHeight: '1.2' }}>{cat.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: '18px', position: 'relative', zIndex: 1 }}>
          <textarea className="input" placeholder="Additional details (optional)..."
            value={description} onChange={(e) => setDescription(e.target.value)}
            rows={2}
            style={{ resize: 'none', fontSize: '13px', lineHeight: '1.5' }}
          />
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '10px', position: 'relative', zIndex: 1 }}>
          <button className="btn btn-ghost" style={{ flex: 1, fontSize: '13px' }} onClick={onClose}>Cancel</button>
          <button id="submit-danger-pin-btn" className="btn btn-danger"
            style={{ flex: 2, fontSize: '13px' }}
            onClick={handleSubmit}
            disabled={!selectedCategory || submitting}
          >
            {submitting ? <><div className="spinner" /><span>Submitting...</span></> : <><span>⚠️</span><span>Report Issue</span></>}
          </button>
        </div>

        <div style={{
          marginTop: '14px', fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px',
          position: 'relative', zIndex: 1,
        }}>
          <span>⏱</span> Pin expires automatically after 24 hours
        </div>
      </div>
    </div>
  );
}
