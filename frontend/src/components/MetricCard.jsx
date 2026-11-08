import React from 'react';

export default function MetricCard({ title, value, unit = '', change, changeType = 'positive', icon: Icon, description }) {
  const isPositive = changeType === 'positive';
  const isNeutral = changeType === 'neutral';
  const isAlert = changeType === 'negative';

  return (
    <div className="industrial-card p-4 hover:border-slate-700">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="w-8 h-8 rounded-md bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-300">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline space-x-1">
        <span className="text-2xl font-bold font-mono text-slate-100 tracking-tight">{value}</span>
        {unit && <span className="text-sm font-mono text-slate-400">{unit}</span>}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        {change && (
          <span
            className={`font-mono px-1.5 py-0.5 rounded text-[10px] font-semibold ${
              isPositive
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : isAlert
                ? 'bg-rose-950 text-rose-400 border border-rose-800'
                : 'bg-slate-800 text-slate-300 border border-slate-700'
            }`}
          >
            {change}
          </span>
        )}
        {description && <span className="text-[11px] text-slate-500 truncate">{description}</span>}
      </div>
    </div>
  );
}
