import React from 'react';
import { Compass, Zap, Anchor } from 'lucide-react';

export default function PresetSelector({ presets, selectedPreset, onSelectPreset, disabled }) {
  if (!presets || presets.length === 0) return null;

  return (
    <div className="bg-sonar-900 border border-sonar-700/60 rounded-lg p-3.5 mb-4">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-sonar-cyan">
          <Zap className="w-3.5 h-3.5" />
          <span>HACKATHON QUICK-DEMO SCENARIOS (1-CLICK TEST)</span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          Realistic Sonar Data
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
        {presets.map((preset) => {
          const isSelected = selectedPreset?.id === preset.id;
          return (
            <button
              key={preset.id}
              onClick={() => onSelectPreset(preset)}
              disabled={disabled}
              className={`text-left p-2.5 rounded-md border text-xs font-mono transition-all ${
                isSelected
                  ? 'bg-sonar-cyan/15 border-sonar-cyan text-white shadow-[0_0_10px_rgba(0,229,255,0.2)]'
                  : 'bg-sonar-850/70 border-sonar-700/50 text-slate-300 hover:border-sonar-600 hover:bg-sonar-800'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center justify-between font-semibold text-slate-200 mb-1 truncate">
                <span className="truncate">{preset.name.split('—')[0]}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-sonar-700/60 text-sonar-cyan">
                  {preset.target_type}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-1">
                {preset.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
