import React from 'react';
import { Shield, Radio, Cpu, Activity, Download, FileText } from 'lucide-react';

export default function Header({ systemHealth, analysisResult, onOpenReport }) {
  const isAiMode = systemHealth?.mode === 'AI';

  return (
    <header className="bg-sonar-900/90 border-b border-sonar-700/60 backdrop-blur-md sticky top-0 z-50 px-4 lg:px-6 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Brand & MoES Info */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-sonar-cyan/10 border border-sonar-cyan/30 text-sonar-cyan shadow-[0_0_15px_rgba(0,229,255,0.25)]">
            <Radio className="w-6 h-6 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sonar-emerald opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-sonar-emerald"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg tracking-wider text-white flex items-center gap-2">
                SONARSENTINEL
                <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-sonar-700/60 text-sonar-cyan border border-sonar-600">
                  SIH26057 • MoES
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Automated Underwater Debris & Acoustic Anomaly Detection System
            </p>
          </div>
        </div>

        {/* Right: Status Indicators & Actions */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Online Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-sonar-850 border border-sonar-700/70 text-xs font-mono">
            <Activity className="w-3.5 h-3.5 text-sonar-emerald" />
            <span className="text-slate-300">SYSTEM:</span>
            <span className="text-sonar-emerald font-semibold">
              {systemHealth ? 'ONLINE' : 'CONNECTING...'}
            </span>
          </div>

          {/* Mode Indicator (Demo vs AI) */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-mono ${
            isAiMode
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
              : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
          }`}>
            <Cpu className="w-3.5 h-3.5" />
            <span>MODE:</span>
            <span className="font-bold tracking-wide">
              {isAiMode ? 'AI INFERENCE (YOLOv8)' : 'DEMO MODE (ACOUSTIC HEURISTIC)'}
            </span>
          </div>

          {/* Mission Report Button */}
          {analysisResult && (
            <button
              onClick={onOpenReport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sonar-cyan/15 hover:bg-sonar-cyan/25 border border-sonar-cyan/40 text-sonar-cyan hover:text-white transition-all text-xs font-mono font-medium shadow-[0_0_10px_rgba(0,229,255,0.15)]"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>MISSION REPORT</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
