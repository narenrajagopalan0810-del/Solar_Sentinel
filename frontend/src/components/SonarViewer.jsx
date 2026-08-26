import React, { useState } from 'react';
import { Eye, Layers, ZoomIn, Sliders, Scan, Crosshair } from 'lucide-react';

export default function SonarViewer({
  analysisResult,
  selectedDetection,
  onSelectDetection,
  isAnalyzing
}) {
  const [viewMode, setViewMode] = useState('annotated'); // 'annotated' | 'preprocessed' | 'original'

  if (isAnalyzing) {
    return (
      <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-6 flex flex-col items-center justify-center min-h-[420px] relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-sonar-cyan/10 via-transparent to-transparent opacity-60"></div>
        
        {/* Radar Scanner Animation */}
        <div className="relative w-44 h-44 rounded-full border border-sonar-cyan/30 flex items-center justify-center mb-6">
          <div className="absolute inset-0 rounded-full border border-sonar-cyan/20 scale-75"></div>
          <div className="absolute inset-0 rounded-full border border-sonar-cyan/15 scale-50"></div>
          <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-sonar-cyan to-transparent animate-radar origin-center"></div>
          <Scan className="w-8 h-8 text-sonar-cyan animate-pulse" />
        </div>

        <h3 className="text-sm font-mono font-bold text-white tracking-widest uppercase mb-1">
          Processing Sonar Imagery
        </h3>
        <p className="text-xs font-mono text-slate-400 text-center max-w-sm">
          Bilateral Despeckling • CLAHE Contrast Boost • YOLOv8 Feature Scan • Acoustic Shadow Analysis
        </p>
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-8 flex flex-col items-center justify-center min-h-[420px] text-center">
        <div className="w-16 h-16 rounded-full bg-sonar-850 border border-sonar-700 flex items-center justify-center text-slate-500 mb-4">
          <Layers className="w-8 h-8" />
        </div>
        <h3 className="text-sm font-mono font-bold text-slate-200 uppercase tracking-wider mb-1">
          Acoustic Visualization Viewport
        </h3>
        <p className="text-xs font-mono text-slate-400 max-w-md">
          Upload a side-scan or forward-looking sonar record, or choose a 1-click survey preset from the top banner to inspect automated debris & anomaly detections.
        </p>
      </div>
    );
  }

  const currentImage =
    viewMode === 'annotated'
      ? analysisResult.annotated_image_url
      : viewMode === 'preprocessed'
      ? analysisResult.preprocessed_image_url
      : analysisResult.original_image_url;

  return (
    <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg overflow-hidden flex flex-col">
      {/* Viewport Top Bar */}
      <div className="p-3 bg-sonar-850 border-b border-sonar-700/70 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-slate-200 tracking-wider">
            SONAR SWATH INSPECTOR
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sonar-800 text-sonar-cyan border border-sonar-700">
            {analysisResult.image_width} × {analysisResult.image_height} PX
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sonar-800 text-slate-300 border border-sonar-700">
            {analysisResult.processing_time_ms} ms
          </span>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center bg-sonar-900 p-0.5 rounded border border-sonar-700/80 text-[11px] font-mono">
          <button
            onClick={() => setViewMode('annotated')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1 ${
              viewMode === 'annotated'
                ? 'bg-sonar-cyan text-slate-950 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Crosshair className="w-3 h-3" />
            AI Detections
          </button>
          <button
            onClick={() => setViewMode('preprocessed')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1 ${
              viewMode === 'preprocessed'
                ? 'bg-sonar-cyan text-slate-950 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3 h-3" />
            CLAHE Enhanced
          </button>
          <button
            onClick={() => setViewMode('original')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1 ${
              viewMode === 'original'
                ? 'bg-sonar-cyan text-slate-950 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Eye className="w-3 h-3" />
            Raw Sonar
          </button>
        </div>
      </div>

      {/* Main Image Stage */}
      <div className="relative bg-black flex items-center justify-center p-2 min-h-[380px] select-none">
        {/* Sonar Swath Legend / Nadir line marker */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2 pointer-events-none">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/70 text-slate-300 border border-slate-700">
            PORT SWATH
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sonar-cyan/20 text-sonar-cyan border border-sonar-cyan/40">
            NADIR (CENTER TRACK)
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/70 text-slate-300 border border-slate-700">
            STARBOARD SWATH
          </span>
        </div>

        {/* Display Image */}
        <img
          src={currentImage}
          alt="Sonar Visualization"
          className="max-h-[500px] w-full object-contain rounded border border-sonar-800"
        />
      </div>

      {/* Detections Fast Selector Tray */}
      {analysisResult.detections?.length > 0 && (
        <div className="p-2.5 bg-sonar-850 border-t border-sonar-700/70 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-mono text-slate-400 font-semibold uppercase tracking-wider flex-shrink-0">
            Targets ({analysisResult.detections.length}):
          </span>
          {analysisResult.detections.map((det) => {
            const isSelected = selectedDetection?.id === det.id;
            return (
              <button
                key={det.id}
                onClick={() => onSelectDetection(det)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono border transition-all flex-shrink-0 ${
                  isSelected
                    ? 'bg-sonar-cyan/20 border-sonar-cyan text-white shadow-[0_0_8px_rgba(0,229,255,0.3)]'
                    : 'bg-sonar-900 border-sonar-700/60 text-slate-300 hover:border-sonar-600'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${
                  det.hazard_level === 'CRITICAL' ? 'bg-rose-500' :
                  det.hazard_level === 'HIGH' ? 'bg-amber-500' :
                  det.hazard_level === 'MEDIUM' ? 'bg-yellow-400' : 'bg-cyan-400'
                }`} />
                <span>{det.class_name}</span>
                <span className="text-[10px] text-slate-400">({Math.round(det.final_score * 100)}%)</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
