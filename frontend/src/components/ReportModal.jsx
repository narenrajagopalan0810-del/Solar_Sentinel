import React from 'react';
import { X, Download, FileJson, FileSpreadsheet, Globe, Shield, CheckCircle2 } from 'lucide-react';
import { getReportDownloadUrl } from '../services/api';

export default function ReportModal({ isOpen, onClose, analysisResult }) {
  if (!isOpen || !analysisResult) return null;

  const {
    mission_id, timestamp, mode, model_name,
    navigation, detections, summary, processing_time_ms
  } = analysisResult;

  const jsonUrl = getReportDownloadUrl(mission_id, 'json');
  const csvUrl = getReportDownloadUrl(mission_id, 'csv');
  const geojsonUrl = getReportDownloadUrl(mission_id, 'geojson');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-sonar-900 border border-sonar-700 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 bg-sonar-850 border-b border-sonar-700/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded bg-sonar-cyan/10 border border-sonar-cyan/30 text-sonar-cyan">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-mono font-bold text-white tracking-wider">
                SONARSENTINEL MISSION INTELLIGENCE REPORT
              </h2>
              <p className="text-xs font-mono text-slate-400">
                Mission ID: <span className="text-sonar-cyan font-bold">{mission_id}</span> • {timestamp}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-sonar-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4 font-mono text-xs">
          {/* Mission Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-sonar-850 p-3 rounded-lg border border-sonar-700/60">
            <div>
              <span className="text-[10px] text-slate-400 block">PIPELINE MODE</span>
              <span className="font-bold text-sonar-cyan">{mode} ({model_name})</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">VESSEL POSITION</span>
              <span className="font-bold text-white">{navigation.vessel_lat}°N, {navigation.vessel_lon}°E</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">HEADING & ALTITUDE</span>
              <span className="font-bold text-white">{navigation.heading}° True / {navigation.altitude}m Alt</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">PROCESSING DURATION</span>
              <span className="font-bold text-emerald-400">{processing_time_ms} ms</span>
            </div>
          </div>

          {/* Detections Table */}
          <div>
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Identified Underwater Obstacles ({detections.length})
            </h3>
            <div className="overflow-x-auto border border-sonar-700/60 rounded-lg">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead className="bg-sonar-850 text-slate-400 border-b border-sonar-700/60">
                  <tr>
                    <th className="p-2.5">ID</th>
                    <th className="p-2.5">Class</th>
                    <th className="p-2.5">Hazard Level</th>
                    <th className="p-2.5">AI Conf.</th>
                    <th className="p-2.5">Physics Score</th>
                    <th className="p-2.5">Final Rating</th>
                    <th className="p-2.5">Shadow Verified</th>
                    <th className="p-2.5">WGS84 Lat/Lon</th>
                    <th className="p-2.5">Slant Range</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sonar-800 text-slate-200">
                  {detections.map((det) => (
                    <tr key={det.id} className="hover:bg-sonar-850/50">
                      <td className="p-2.5 font-bold text-sonar-cyan">{det.id}</td>
                      <td className="p-2.5 uppercase font-medium">{det.class_name}</td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          det.hazard_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                          det.hazard_level === 'HIGH' ? 'bg-amber-500/20 text-amber-300' :
                          det.hazard_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-cyan-500/20 text-cyan-300'
                        }`}>
                          {det.hazard_level}
                        </span>
                      </td>
                      <td className="p-2.5">{Math.round(det.model_confidence * 100)}%</td>
                      <td className="p-2.5">{Math.round(det.acoustic_score * 100)}%</td>
                      <td className="p-2.5 font-bold text-white">{Math.round(det.final_score * 100)}%</td>
                      <td className="p-2.5">
                        {det.shadow_detected ? (
                          <span className="text-emerald-400 font-semibold">CONFIRMED</span>
                        ) : (
                          <span className="text-slate-500">NO</span>
                        )}
                      </td>
                      <td className="p-2.5">{det.latitude.toFixed(5)}°, {det.longitude.toFixed(5)}°</td>
                      <td className="p-2.5">{det.geo_details.slant_range_m}m</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer & Export Buttons */}
        <div className="p-4 bg-sonar-850 border-t border-sonar-700/80 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[11px] font-mono text-slate-400">
            Export formats for GIS & Hydrographic Analysis:
          </div>

          <div className="flex items-center gap-2">
            <a
              href={jsonUrl}
              download={`SonarSentinel_${mission_id}.json`}
              className="flex items-center gap-1.5 px-3 py-2 rounded bg-sonar-800 hover:bg-sonar-700 border border-sonar-600 text-white font-mono text-xs transition-colors"
            >
              <FileJson className="w-3.5 h-3.5 text-sonar-cyan" />
              Download JSON
            </a>

            <a
              href={csvUrl}
              download={`SonarSentinel_${mission_id}.csv`}
              className="flex items-center gap-1.5 px-3 py-2 rounded bg-sonar-800 hover:bg-sonar-700 border border-sonar-600 text-white font-mono text-xs transition-colors"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-sonar-emerald" />
              Download CSV
            </a>

            <a
              href={geojsonUrl}
              download={`SonarSentinel_${mission_id}.geojson`}
              className="flex items-center gap-1.5 px-3 py-2 rounded bg-sonar-800 hover:bg-sonar-700 border border-sonar-600 text-white font-mono text-xs transition-colors"
            >
              <Globe className="w-3.5 h-3.5 text-sonar-amber" />
              Download GeoJSON
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
