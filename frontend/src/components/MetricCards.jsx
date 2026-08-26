import React from 'react';
import { Target, AlertTriangle, Disc, HelpCircle, ShieldAlert } from 'lucide-react';

export default function MetricCards({ summary, processingTimeMs, missionId }) {
  const s = summary || {
    total_detections: 0,
    critical_hazards: 0,
    high_hazards: 0,
    ghost_nets: 0,
    unknown_anomalies: 0,
  };

  const highOrCritical = (s.critical_hazards || 0) + (s.high_hazards || 0);

  const cards = [
    {
      title: 'TOTAL DETECTIONS',
      value: s.total_detections ?? 0,
      subtext: missionId ? `Mission: ${missionId}` : 'Awaiting Sonar Ingestion',
      icon: Target,
      color: 'text-sonar-cyan',
      borderColor: 'border-sonar-cyan/30',
      bgColor: 'bg-sonar-cyan/5',
      glow: 'shadow-[0_0_15px_rgba(0,229,255,0.08)]',
    },
    {
      title: 'HIGH-RISK / CRITICAL',
      value: highOrCritical,
      subtext: `${s.critical_hazards || 0} Critical, ${s.high_hazards || 0} High`,
      icon: ShieldAlert,
      color: 'text-rose-400',
      borderColor: 'border-rose-500/30',
      bgColor: 'bg-rose-500/5',
      glow: highOrCritical > 0 ? 'shadow-[0_0_15px_rgba(244,63,94,0.15)]' : '',
    },
    {
      title: 'GHOST NETS',
      value: s.ghost_nets ?? 0,
      subtext: 'Entanglement & Ecological Threat',
      icon: AlertTriangle,
      color: 'text-amber-400',
      borderColor: 'border-amber-500/30',
      bgColor: 'bg-amber-500/5',
      glow: '',
    },
    {
      title: 'UNKNOWN ANOMALIES',
      value: (s.unknown_anomalies || 0) + (s.wreckages || 0),
      subtext: `${s.wreckages || 0} Wrecks, ${s.unknown_anomalies || 0} Unclassified`,
      icon: HelpCircle,
      color: 'text-indigo-400',
      borderColor: 'border-indigo-500/30',
      bgColor: 'bg-indigo-500/5',
      glow: '',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`p-4 rounded-lg bg-sonar-900 border ${c.borderColor} ${c.bgColor} ${c.glow} flex flex-col justify-between transition-all hover:translate-y-[-1px]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono tracking-wider font-semibold text-slate-400">
                {c.title}
              </span>
              <Icon className={`w-4 h-4 ${c.color}`} />
            </div>
            <div className="my-2">
              <span className="text-2xl lg:text-3xl font-bold font-mono tracking-tight text-white">
                {c.value}
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-400 truncate">
              {c.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
}
