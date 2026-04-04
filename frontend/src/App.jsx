import { useState, useEffect } from 'react';
import Map from './components/Map';
import SearchPanel from './components/SearchPanel';
import SafetyHUD from './components/SafetyHUD';
import SOSButton from './components/SOSButton';
import DangerPinModal from './components/DangerPinModal';
import GuardianLink from './components/GuardianLink';
import DashboardStats from './components/LiveStats';
import LoadingScreen from './components/LoadingScreen';
import { offlineRouter } from './offline/OfflineRouter';
import { useRouting } from './hooks/useRouting';
import { useGeolocation } from './hooks/useGeolocation';
import { useDangerPins } from './hooks/useDangerPins';
import { useSafetySocket } from './hooks/useSafetySocket';
import './index.css';

/* ── Main Application ──────────────────────────────────────── */
export default function App() {
  const { routes, loading, error, calculateRoute, clearRoute } = useRouting();
  const { location: userLocation } = useGeolocation();
  const { pins, createPin, fetchPins } = useDangerPins();

  // Initialize Real-time Safety Mesh WebSockets
  const { sendLocation } = useSafetySocket(fetchPins);

  const [dangerPinTarget, setDangerPinTarget] = useState(null);
  const [showGuardian, setShowGuardian] = useState(false);
  const [activeRouteIndex, setActiveRouteIndex] = useState(0);
  const [isNavigating, setIsNavigating] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);

  // Broadcast Live Location when navigating
  useEffect(() => {
    if (isNavigating && userLocation && routes?.[activeRouteIndex]?.guardian_token) {
      sendLocation(userLocation.lat, userLocation.lng, routes[activeRouteIndex].guardian_token);
    }
  }, [userLocation, isNavigating, activeRouteIndex, routes, sendLocation]);
  
  const [appInitializing, setAppInitializing] = useState(true);
  const [initMsg, setInitMsg] = useState("Booting Night Navigator...");

  useEffect(() => {
    async function init() {
      try {
        setInitMsg("Syncing Jaipur Offline Network (48MB)...");
        await offlineRouter.initialize();
      } catch (e) {
        console.error("Offline sync failed, operating in online-only mode:", e);
      } finally {
        setTimeout(() => setAppInitializing(false), 800);
      }
    }
    init();
  }, []);

  const handleRouteRequest = async (startCoords, endCoords, vehicleType) => {
    await calculateRoute(startCoords, endCoords, vehicleType);
    setActiveRouteIndex(0);
    setIsNavigating(false);
  };

  const handleMapClick = (lngLat) => {
    setDangerPinTarget(lngLat);
  };

  const handlePinSubmit = async (lat, lng, category, description) => {
    await createPin(lat, lng, category, description);
    setDangerPinTarget(null);
  };

  if (appInitializing) {
    return <LoadingScreen statusMessage={initMsg} />;
  }

  return (
    <div className="app-container animate-fade-in">
      {/* Map */}
      <Map
        routes={routes}
        activeRouteIndex={activeRouteIndex}
        dangerPins={pins}
        userLocation={userLocation}
        onMapClick={handleMapClick}
        isNavigating={isNavigating}
      />

      {/* Search Panel */}
      <SearchPanel
        onRouteRequest={handleRouteRequest}
        loading={loading}
        routes={routes}
        activeRouteIndex={activeRouteIndex}
        onSelectRoute={setActiveRouteIndex}
        onClear={clearRoute}
        isNavigating={isNavigating}
        setIsNavigating={setIsNavigating}
        userLocation={userLocation}
      />

      {/* Safety HUD & Dashboard Stats */}
      {!isNavigating && (
        <>
          <SafetyHUD route={routes?.[activeRouteIndex]} dangerPins={pins} />
          <DashboardStats />
        </>
      )}

      {/* SOS */}
      <SOSButton
        guardianToken={routes?.[activeRouteIndex]?.guardian_token}
        onShareGuardian={() => setShowGuardian(true)}
      />

      {/* Error Toast */}
      {error && (
        <div className="toast" style={{ borderLeft: '4px solid var(--danger)' }}>
          <span style={{ color: 'var(--text-primary)' }}>{error}</span>
        </div>
      )}

      {/* Danger Pin Modal */}
      {dangerPinTarget && (
        <DangerPinModal
          location={dangerPinTarget}
          onSubmit={handlePinSubmit}
          onClose={() => setDangerPinTarget(null)}
        />
      )}

      {/* Guardian Link Modal */}
      {showGuardian && routes?.[activeRouteIndex]?.guardian_token && (
        <GuardianLink
          token={routes[activeRouteIndex].guardian_token}
          onClose={() => setShowGuardian(false)}
        />
      )}

      {/* Navigation Controls */}
      {isNavigating && (
        <>
          <button className="btn btn-danger animate-slide-up nav-cancel-btn"
            onClick={() => setIsNavigating(false)}>
            End Navigation
          </button>

          <button className="nav-report-btn animate-scale-in"
            onClick={() => {
              const loc = userLocation || (routes?.[activeRouteIndex]?.coordinates?.[0] ? {
                lat: routes[activeRouteIndex].coordinates[0][0],
                lng: routes[activeRouteIndex].coordinates[0][1]
              } : null);
              if (loc) setDangerPinTarget(loc);
              else alert("Location unavailable");
            }}>Report Hazard</button>

          <button className="nav-audio-btn animate-scale-in"
            onClick={() => setAudioEnabled(!audioEnabled)}
            style={{
              borderColor: audioEnabled ? 'var(--primary)' : 'var(--border-light)',
              color: audioEnabled ? 'var(--primary)' : 'var(--text-muted)'
            }}
            title={audioEnabled ? 'Audio Guidance ON' : 'Audio Guidance OFF'}
          >
            {audioEnabled ? '🔊' : '🔇'}
          </button>
        </>
      )}

      {/* Brand Badge */}
      <div className="brand-badge" style={{ 
        top: isNavigating ? '20px' : 'auto', 
        bottom: isNavigating ? 'auto' : '40px',
        right: isNavigating ? '20px' : '104px'
      }}>
        <span className="dot" />
        Jaipur
      </div>
    </div>
  );
}
