import React from 'react';
import { 
  ShieldCheck, AlertTriangle, Crosshair, MapPin, 
  Activity, ArrowRight, CheckCircle2, XCircle, Info 
} from 'lucide-react';

export default function DetectionInspector({ detection, vesselPos }) {
  if (!detection) {
    return (
      <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-5 flex flex-col items-center justify-center min-h-[320px] text-center">
        <Crosshair className="w-10 h-10 text-slate-600 mb-3" />
        <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-1">
          Acoustic Anomaly Inspector
        </h4>
        <p className="text-xs font-mono text-slate-500 max-w-xs">
          Select any detection above or click a map marker to inspect its physics verification metrics and calculated coordinates.
        </p>
      </div>
    );
  }

  const {
    id, class_name, model_confidence, acoustic_score, final_score,
    hazard_level, shadow_detected, latitude, longitude,
    physics_details, geo_details, crop_image_url
  } = detection;

  const hazardColor = 
    hazard_level === 'CRITICAL' ? 'text-rose-400 bg-rose-500/10 border-rose-500/30' :
    hazard_level === 'HIGH' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
    hazard_level === 'MEDIUM' ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30' :
    'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';

  return (
    <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-sonar-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">{id}</span>
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              {class_name.replace('_', ' ')}
            </h3>
          </div>
          <p className="text-[10px] font-mono text-slate-400 mt-0.5">
            Physics-Validated Underwater Obstacle
          </p>
        </div>

        <div className={`px-2.5 py-1 rounded border text-xs font-mono font-bold tracking-wider ${hazardColor}`}>
          {hazard_level} HAZARD ({Math.round(final_score * 100)}%)
        </div>
      </div>

      {/* Signature & Score Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Left: Cropped Signature */}
        <div className="bg-sonar-850 border border-sonar-700/60 rounded p-2.5 flex flex-col items-center justify-center">
          <span className="text-[10px] font-mono text-slate-400 mb-2 uppercase tracking-wider">
            Acoustic ROI Signature
          </span>
          {crop_image_url ? (
            <img
              src={crop_image_url}
              alt="Target Signature"
              className="max-h-24 object-contain rounded border border-sonar-700 bg-black"
            />
          ) : (
            <div className="w-20 h-20 rounded bg-black flex items-center justify-center text-slate-600 text-xs font-mono">
              ROI
            </div>
          )}
          <span className="text-[10px] font-mono text-sonar-cyan mt-2">
            {Math.round(detection.bbox.width || 0)}×{Math.round(detection.bbox.height || 0)} px
          </span>
        </div>

        {/* Middle & Right: Multi-Score Fusion */}
        <div className="md:col-span-2 bg-sonar-850 border border-sonar-700/60 rounded p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono mb-1">
              <span className="text-slate-300 flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-sonar-cyan" />
                YOLOv8 Model Confidence:
              </span>
              <span className="font-bold text-white">{Math.round(model_confidence * 100)}%</span>
            </div>
            <div className="w-full bg-sonar-900 rounded-full h-2 mb-3 overflow-hidden">
              <div
                className="bg-sonar-cyan h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.round(model_confidence * 100)}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-xs font-mono mb-1">
              <span className="text-slate-300 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-sonar-emerald" />
                Acoustic Physics Score:
              </span>
              <span className="font-bold text-white">{Math.round(acoustic_score * 100)}%</span>
            </div>
            <div className="w-full bg-sonar-900 rounded-full h-2 mb-2 overflow-hidden">
              <div
                className="bg-sonar-emerald h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.round(acoustic_score * 100)}%` }}
              />
            </div>
          </div>

          <div className="pt-2 border-t border-sonar-700/60 flex items-center justify-between text-[11px] font-mono">
            <span className="text-slate-400">Hazard Score Formula:</span>
            <span className="text-sonar-cyan font-semibold">
              0.65×(AI) + 0.35×(Physics) = <span className="text-white">{final_score}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Physics Validation Details */}
      <div className="bg-sonar-850 border border-sonar-700/60 rounded p-3">
        <div className="flex items-center justify-between mb-2 pb-1 border-b border-sonar-700/40">
          <span className="text-[11px] font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-sonar-emerald" />
            Physics-Informed Acoustic Filter Analysis
          </span>
          <div className={`flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded ${
            shadow_detected ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/40' : 'bg-rose-950/60 text-rose-300 border border-rose-500/40'
          }`}>
            {shadow_detected ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
            <span>{shadow_detected ? 'SHADOW CONFIRMED' : 'NO SHADOW DETECTED'}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono mb-2">
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Highlight Peak</span>
            <span className="font-bold text-white">{physics_details.highlight_mean_intensity} / 255</span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Shadow Base</span>
            <span className="font-bold text-white">{physics_details.shadow_mean_intensity} / 255</span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Contrast Ratio</span>
            <span className="font-bold text-sonar-cyan">{physics_details.contrast_ratio}x</span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Shadow Extent</span>
            <span className="font-bold text-white">{physics_details.shadow_length_px} px</span>
          </div>
        </div>

        <p className="text-[10px] font-mono text-slate-400 italic">
          {physics_details.heuristic_notes}
        </p>
      </div>

      {/* Geolocation & Slant Range Engine */}
      <div className="bg-sonar-850 border border-sonar-700/60 rounded p-3">
        <div className="flex items-center justify-between mb-2 pb-1 border-b border-sonar-700/40">
          <span className="text-[11px] font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-sonar-amber" />
            Estimated WGS84 Geolocation & Sonar Ranges
          </span>
          <span className="text-[10px] font-mono text-sonar-amber bg-sonar-amber/10 px-2 py-0.5 rounded border border-sonar-amber/20">
            {geo_details.estimation_method}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Est. Latitude</span>
            <span className="font-bold text-white">{latitude.toFixed(6)}° N</span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Est. Longitude</span>
            <span className="font-bold text-white">{longitude.toFixed(6)}° E</span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Cross-Track Dist</span>
            <span className="font-bold text-sonar-cyan">
              {geo_details.cross_track_m > 0 ? `+${geo_details.cross_track_m}m (Stbd)` : `${geo_details.cross_track_m}m (Port)`}
            </span>
          </div>
          <div className="bg-sonar-900 p-2 rounded border border-sonar-700/40">
            <span className="text-[10px] text-slate-400 block">Slant Range</span>
            <span className="font-bold text-white">{geo_details.slant_range_m} m</span>
          </div>
        </div>
      </div>
    </div>
  );
}
