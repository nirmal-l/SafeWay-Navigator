import { useState, useEffect, useRef } from 'react';

export function useGeolocation() {
  const [location, setLocation] = useState(null); // { lat, lng }
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const watchIdRef = useRef(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      // Fallback to Jaipur city center for demo — set via timeout to keep it async
      const id = setTimeout(() => {
        setLocation({ lat: 26.9124, lng: 75.7873 });
        setLoading(false);
      }, 0);
      return () => clearTimeout(id);
    }

    // First, get a quick position
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLoading(false);
      },
      () => {
        // Fallback to Jaipur city center
        setLocation({ lat: 26.9124, lng: 75.7873 });
        setLoading(false);
        setError('Using Jaipur city center as fallback location');
      },
      { timeout: 5000, enableHighAccuracy: false }
    );

    // Then, watch for updates
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      },
      () => {}, // Silent fail on watch errors
      { enableHighAccuracy: true, maximumAge: 10000 }
    );

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return { location, error, loading };
}
