import React from 'react';
import { Upload, Navigation, Compass, Waves, Crosshair, Play, RefreshCw, Layers } from 'lucide-react';

export default function TelemetryControl({
  file,
  previewUrl,
  telemetry,
  isAnalyzing,
  onFileChange,
  onTelemetryChange,
  onAnalyze,
  onReset
}) {
  const handleInputChange = (field, value) => {
    onTelemetryChange({
      ...telemetry,
      [field]: value
    });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileChange(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-sonar-800">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-white tracking-wider">
          <Crosshair className="w-4 h-4 text-sonar-cyan" />
          <span>MISSION TELEMETRY & INGESTION</span>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 font-mono transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Reset
        </button>
      </div>

      {/* File Ingestion Dropzone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-3 text-center transition-all ${
          file
            ? 'border-sonar-cyan/60 bg-sonar-cyan/5'
            : 'border-sonar-700 hover:border-sonar-600 bg-sonar-850/50'
        }`}
      >
        <input
          type="file"
          id="sonar-upload"
          accept="image/*,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
          onChange={(e) => e.target.files?.[0] && onFileChange(e.target.files[0])}
          className="hidden"
        />

        {previewUrl ? (
          <div className="flex items-center gap-3">
            <img
              src={previewUrl}
              alt="Sonar Preview"
              className="w-16 h-16 object-cover rounded border border-sonar-700 bg-black"
            />
            <div className="flex-1 text-left">
              <p className="text-xs font-mono font-medium text-white truncate max-w-[180px]">
                {file?.name || 'Sonar Imagery Loaded'}
              </p>
              <p className="text-[10px] font-mono text-slate-400">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Preset Matrix Loaded'}
              </p>
              <label
                htmlFor="sonar-upload"
                className="mt-1 inline-block text-[11px] font-mono text-sonar-cyan hover:underline cursor-pointer"
              >
                Change Image
              </label>
            </div>
          </div>
        ) : (
          <label htmlFor="sonar-upload" className="cursor-pointer block py-3">
            <Upload className="w-6 h-6 text-sonar-cyan mx-auto mb-1.5 opacity-80" />
            <p className="text-xs font-mono font-medium text-slate-200">
              Drag & Drop Sonar Image
            </p>
            <p className="text-[10px] font-mono text-slate-400 mt-0.5">
              Supports Side-Scan (SSS) & Forward-Looking (FLS) formats
            </p>
          </label>
        )}
      </div>

      {/* Navigation Telemetry Parameters */}
      <div className="space-y-3">
        <div className="text-[11px] font-mono font-semibold text-slate-400 flex items-center gap-1.5">
          <Navigation className="w-3.5 h-3.5 text-sonar-cyan" />
          <span>Vessel & Sensor Navigation Telemetry</span>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">
              Vessel Lat (°N)
            </label>
            <input
              type="number"
              step="0.0001"
              value={telemetry.vessel_lat}
              onChange={(e) => handleInputChange('vessel_lat', parseFloat(e.target.value) || 0)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">
              Vessel Lon (°E)
            </label>
            <input
              type="number"
              step="0.0001"
              value={telemetry.vessel_lon}
              onChange={(e) => handleInputChange('vessel_lon', parseFloat(e.target.value) || 0)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1 flex items-center gap-1">
              <Compass className="w-3 h-3 text-sonar-amber" />
              Heading (0-360°)
            </label>
            <input
              type="number"
              min="0"
              max="360"
              value={telemetry.heading}
              onChange={(e) => handleInputChange('heading', parseFloat(e.target.value) || 0)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1 flex items-center gap-1">
              <Waves className="w-3 h-3 text-sonar-cyan" />
              Towfish Alt. (m)
            </label>
            <input
              type="number"
              min="1"
              max="200"
              value={telemetry.altitude}
              onChange={(e) => handleInputChange('altitude', parseFloat(e.target.value) || 1)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">
              Swath Width (m)
            </label>
            <input
              type="number"
              min="10"
              max="500"
              value={telemetry.swath_width_m}
              onChange={(e) => handleInputChange('swath_width_m', parseFloat(e.target.value) || 100)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">
              Mission Tag
            </label>
            <input
              type="text"
              value={telemetry.mission_name}
              onChange={(e) => handleInputChange('mission_name', e.target.value)}
              className="w-full bg-sonar-850 border border-sonar-700/80 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-sonar-cyan"
            />
          </div>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={onAnalyze}
        disabled={isAnalyzing || (!file && !previewUrl)}
        className={`w-full py-2.5 px-4 rounded-lg font-mono font-semibold text-xs tracking-wider flex items-center justify-center gap-2 transition-all ${
          isAnalyzing
            ? 'bg-sonar-700 text-slate-400 cursor-not-allowed'
            : !file && !previewUrl
            ? 'bg-sonar-800 text-slate-500 cursor-not-allowed border border-sonar-700'
            : 'bg-gradient-to-r from-sonar-cyan/90 to-emerald-400 text-slate-950 hover:brightness-110 shadow-[0_0_20px_rgba(0,229,255,0.3)]'
        }`}
      >
        {isAnalyzing ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin text-sonar-cyan" />
            <span>RUNNING ACOUSTIC PIPELINE...</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4 fill-current" />
            <span>RUN SONAR ANALYSIS</span>
          </>
        )}
      </button>
    </div>
  );
}
