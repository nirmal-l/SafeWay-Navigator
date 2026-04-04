import { useState, useCallback } from 'react';
import { offlineRouter } from '../offline/OfflineRouter';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';  // Empty = use Vite proxy locally

export function useRouting() {
  const [routes, setRoutes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateRoute = useCallback(async (startCoords, endCoords, vehicleType = 'walk') => {
    // startCoords and endCoords are [lat, lng]
    setLoading(true);
    setError(null);
    setRoutes(null);

    let isOfflineFallback = false;

    try {
      const res = await fetch(`${BACKEND_URL}/api/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start: startCoords,  // [lat, lng]
          end: endCoords,      // [lat, lng]
          vehicle_type: vehicleType,
        }),
      });

      if (!res.ok) {
        let errMessage = `Server error (Status: ${res.status})`;
        try {
          const err = await res.json();
          if (err && err.detail) errMessage = err.detail;
        } catch (_) {
          // Response body was empty or not JSON
        }
        throw new Error(errMessage);
      }

      const data = await res.json();
      setRoutes(data);
      setLoading(false);
      return data;
      
    } catch (err) {
      if (err.name === 'TypeError' || err.message === 'Failed to fetch' || err.message.includes('Server error')) {
        console.warn('⚠️ Network or server error. Falling back to Jaipur Offline Architecture...');
        isOfflineFallback = true;
      } else {
        setError(err.message);
        setLoading(false);
        return null;
      }
    }

    if (isOfflineFallback) {
      try {
        const offlineData = await offlineRouter.calculateRoute(startCoords, endCoords);
        setRoutes(offlineData);
        setLoading(false);
        return offlineData;
      } catch (offlineErr) {
        console.error("Offline Engine failed:", offlineErr);
        setError("Network offline and area not cached locally.");
        setLoading(false);
        return null;
      }
    }
  }, []);

  const clearRoute = useCallback(() => {
    setRoutes(null);
    setError(null);
  }, []);

  return { routes, loading, error, calculateRoute, clearRoute };
}
