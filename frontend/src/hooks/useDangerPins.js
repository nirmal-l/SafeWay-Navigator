import { useState, useEffect, useCallback } from 'react';

export function useDangerPins() {
  const [pins, setPins] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchPins = useCallback(async () => {
    try {
      const res = await fetch('/api/danger-pins');
      if (res.ok) {
        const data = await res.json();
        setPins(data);
      }
    } catch {
      // Silent fail — pins are optional
    }
  }, []);

  const createPin = useCallback(async (lat, lng, category, description = '') => {
    setLoading(true);
    try {
      const res = await fetch('/api/danger-pins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lng, category, description }),
      });
      if (res.ok) {
        await fetchPins(); // Refresh
        return true;
      }
    } catch {
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchPins]);

  // Initial load + refresh every 30s
  useEffect(() => {
    fetchPins();
    const interval = setInterval(fetchPins, 30000);
    return () => clearInterval(interval);
  }, [fetchPins]);

  return { pins, loading, createPin, fetchPins };
}
