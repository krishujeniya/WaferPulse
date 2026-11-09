import React from 'react';
import { Cpu, Activity, Database, GitMerge, ShieldAlert, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, activeModel, isConnected, isSimulated }) {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: Activity },
    { id: 'pipeline', label: 'Pipeline lab', icon: GitMerge },
    { id: 'models', label: 'Model registry', icon: Layers },
    { id: 'inference', label: 'Inference', icon: Cpu },
    { id: 'monitoring', label: 'Sensor health', icon: ShieldAlert },
  ];

  return (
    <header className="app-header sticky top-0 z-50 border-b border-slate-800 bg-[#080c14]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and System Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#0c1322] border border-cyan-500/30 flex items-center justify-center shadow-[0_0_18px_rgba(6,182,212,0.2)] overflow-hidden">
              <svg viewBox="0 0 120 120" className="w-8 h-8" fill="none">
                <circle cx="60" cy="60" r="52" stroke="#0284c7" strokeWidth="3" fill="#080c14" />
                <circle cx="60" cy="60" r="36" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.6" />
                <rect x="48" y="48" width="10" height="10" rx="1.5" fill="#0284c7" fillOpacity="0.5" stroke="#38bdf8" />
                <rect x="62" y="48" width="10" height="10" rx="1.5" fill="#06b6d4" fillOpacity="0.5" stroke="#22d3ee" />
                <rect x="48" y="62" width="10" height="10" rx="1.5" fill="#10b981" fillOpacity="0.5" stroke="#34d399" />
                <rect x="62" y="62" width="10" height="10" rx="1.5" fill="#0284c7" fillOpacity="0.5" stroke="#38bdf8" />
                <path d="M 18 60 L 36 60 L 42 50 L 48 72 L 54 36 L 62 84 L 70 42 L 76 66 L 82 56 L 88 60 L 102 60" stroke="#38bdf8" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="60" cy="60" r="3.5" fill="#ffffff" />
              </svg>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-100 tracking-tight">Wafer<span className="text-cyan-300">Pulse</span></span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-700/50">
                  MLOps
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Semiconductor Predictive Maintenance</p>
            </div>
          </div>

          {/* Nav items */}
          <nav className="app-nav flex space-x-1 sm:space-x-2" aria-label="Platform sections">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={item.label}
                  className={`interactive-btn flex items-center space-x-2 px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-slate-800 text-sky-400 border border-slate-700 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status indicators */}
          <div className="flex items-center space-x-3">
            {activeModel && (
              <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                <span className="text-slate-500">Active:</span>
                <span className="text-emerald-400 font-medium">{activeModel.version}</span>
              </div>
            )}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : isSimulated ? 'bg-amber-300' : 'bg-rose-400'
                } ${isConnected ? 'animate-pulse' : ''}`}
              />
              <span className="text-slate-300">{isConnected ? 'LIVE FAB' : isSimulated ? 'DEMO FEED' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
