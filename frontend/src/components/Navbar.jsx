import React from 'react';
import { Cpu, Activity, Database, GitMerge, ShieldAlert, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, activeModel, isConnected }) {
  const navItems = [
    { id: 'dashboard', label: 'Fab Dashboard', icon: Activity },
    { id: 'pipeline', label: 'Pipeline Lab', icon: GitMerge },
    { id: 'models', label: 'Model Registry', icon: Layers },
    { id: 'inference', label: 'Inference & Root Cause', icon: Cpu },
    { id: 'monitoring', label: 'Drift & Sensor Health', icon: ShieldAlert },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-[#080c14]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and System Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-sky-950 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-[0_0_15px_rgba(2,132,199,0.25)]">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-100 tracking-tight">WaferGuard</span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-sky-900/50 text-sky-300 border border-sky-700/50">
                  MLOps SaaS
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Semiconductor Predictive Maintenance</p>
            </div>
          </div>

          {/* Nav items */}
          <nav className="flex space-x-1 sm:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
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
                  isConnected ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-amber-400'
                } animate-pulse`}
              />
              <span className="text-slate-400">{isConnected ? 'LIVE FAB' : 'SYNCING'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
