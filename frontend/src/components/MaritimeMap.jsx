import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Compass, Navigation2, AlertOctagon } from 'lucide-react';

// Custom SVG Icons for Leaflet to eliminate broken asset URLs
function createCustomIcon(color, isVessel = false, heading = 0) {
  if (isVessel) {
    const svgHtml = `
      <div style="transform: rotate(${heading}deg); display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="28px" height="28px" style="filter: drop-shadow(0 0 8px ${color});">
          <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/>
        </svg>
      </div>
    `;
    return L.divIcon({
      className: 'custom-vessel-marker',
      html: svgHtml,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  }

  const svgHtml = `
    <div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px;">
      <span style="position: absolute; width: 22px; height: 22px; border-radius: 50%; background: ${color}; opacity: 0.35; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></span>
      <div style="width: 14px; height: 14px; border-radius: 50%; background: ${color}; border: 2px solid #ffffff; box-shadow: 0 0 10px ${color}; z-index: 10;"></div>
    </div>
  `;
  return L.divIcon({
    className: 'custom-target-marker',
    html: svgHtml,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
}

function MapViewController({ center, zoom, bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.isValid && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 17 });
    } else if (center) {
      map.setView(center, zoom || 15);
    }
  }, [center, zoom, bounds, map]);
  return null;
}

export default function MaritimeMap({
  vesselNav,
  detections,
  selectedDetection,
  onSelectDetection,
}) {
  const defaultCenter = [vesselNav?.vessel_lat || 13.0827, vesselNav?.vessel_lon || 80.2707];
  const heading = vesselNav?.heading || 90;

  // Calculate Map Bounds to include vessel and all detected targets
  let bounds = null;
  if (detections && detections.length > 0) {
    const latLngs = [[vesselNav.vessel_lat, vesselNav.vessel_lon]];
    detections.forEach((d) => latLngs.push([d.latitude, d.longitude]));
    bounds = L.latLngBounds(latLngs);
  }

  const getHazardColor = (hazard) => {
    switch (hazard) {
      case 'CRITICAL': return '#f43f5e';
      case 'HIGH': return '#f59e0b';
      case 'MEDIUM': return '#eab308';
      default: return '#00e5ff';
    }
  };

  return (
    <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-3 flex flex-col gap-2 relative">
      <div className="flex items-center justify-between pb-1 border-b border-sonar-800">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
          <Navigation2 className="w-4 h-4 text-sonar-cyan" />
          <span>WGS84 MARITIME GIS GEOLOCATION</span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          OpenStreetMap Marine Grid
        </span>
      </div>

      <div className="h-[360px] w-full rounded overflow-hidden relative border border-sonar-800">
        <MapContainer
          center={defaultCenter}
          zoom={15}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%' }}
        >
          <MapViewController center={defaultCenter} bounds={bounds} />

          {/* CartoDB Dark Matter Marine Tile Layer */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Vessel Swath Range Circle */}
          {vesselNav && (
            <Circle
              center={[vesselNav.vessel_lat, vesselNav.vessel_lon]}
              radius={vesselNav.swath_width_m || 100}
              pathOptions={{
                color: '#00e5ff',
                fillColor: '#00e5ff',
                fillOpacity: 0.04,
                weight: 1,
                dashArray: '4, 6',
              }}
            />
          )}

          {/* Survey Vessel / Towfish Marker */}
          {vesselNav && (
            <Marker
              position={[vesselNav.vessel_lat, vesselNav.vessel_lon]}
              icon={createCustomIcon('#00e5ff', true, heading)}
            >
              <Popup>
                <div className="p-1 font-mono text-xs text-slate-100">
                  <div className="font-bold text-sonar-cyan mb-1 flex items-center gap-1">
                    <Compass className="w-3.5 h-3.5" />
                    SURVEY TOWFISH / AUV
                  </div>
                  <div className="text-[11px] space-y-0.5 text-slate-300">
                    <p>Lat: {vesselNav.vessel_lat.toFixed(6)}°</p>
                    <p>Lon: {vesselNav.vessel_lon.toFixed(6)}°</p>
                    <p>Heading: {heading}° True</p>
                    <p>Altitude: {vesselNav.altitude} m</p>
                  </div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Detected Obstacle / Debris Target Markers */}
          {detections?.map((det) => {
            const markerColor = getHazardColor(det.hazard_level);
            return (
              <Marker
                key={det.id}
                position={[det.latitude, det.longitude]}
                icon={createCustomIcon(markerColor, false)}
                eventHandlers={{
                  click: () => onSelectDetection(det),
                }}
              >
                <Popup>
                  <div className="p-1 font-mono text-xs text-slate-100 min-w-[180px]">
                    <div className="flex items-center justify-between mb-1 pb-1 border-b border-slate-700">
                      <span className="font-bold uppercase text-white">
                        {det.class_name.replace('_', ' ')}
                      </span>
                      <span
                        className="text-[10px] px-1.5 py-0.2 rounded font-bold"
                        style={{ backgroundColor: `${markerColor}33`, color: markerColor }}
                      >
                        {det.hazard_level}
                      </span>
                    </div>

                    <div className="text-[11px] space-y-0.5 text-slate-300">
                      <p>Combined Score: <strong className="text-white">{Math.round(det.final_score * 100)}%</strong></p>
                      <p>Physics Shadow: <strong className="text-white">{det.shadow_detected ? 'CONFIRMED' : 'NO'}</strong></p>
                      <p>Slant Range: <strong className="text-white">{det.geo_details.slant_range_m}m</strong></p>
                      <p className="text-[10px] text-slate-400 mt-1 font-mono">
                        {det.latitude.toFixed(6)}°N, {det.longitude.toFixed(6)}°E
                      </p>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
