import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, CheckCircle2, AlertTriangle, RefreshCw, Wrench, BarChart2, TrendingUp } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { fetchDriftReport } from '../services/api';

export default function Monitoring() {
  const [driftData, setDriftData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchDriftReport();
      setDriftData(data);
    } catch (e) {
      console.error('Failed to load drift report', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const total = driftData?.total_sensors_monitored || 60;
  const stable = driftData?.stable_count || 58;
  const moderate = driftData?.moderate_drift_count || 2;
  const critical = driftData?.critical_drift_count || 0;
  const status = driftData?.overall_status || 'HEALTHY';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800 gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <span>Sensor Drift & Tool Health Monitor</span>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border uppercase ${
                status === 'HEALTHY'
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                  : status === 'WARNING'
                  ? 'bg-amber-950 text-amber-400 border-amber-800'
                  : 'bg-rose-950 text-rose-400 border-rose-800'
              }`}
            >
              {status}
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-mono mt-1">
            Kolmogorov-Smirnov two-sample tests and Population Stability Index (PSI) drift tracking
          </p>
        </div>
        <button
          onClick={loadData}
          className="interactive-btn flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:bg-slate-800"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate Drift</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Channels"
          value={total}
          unit="sensors"
          change="Continuous telemetry"
          changeType="neutral"
          icon={Activity}
          description="Chambers A, B, C"
        />
        <MetricCard
          title="Stable Sensors"
          value={stable}
          unit={`/${total}`}
          change="PSI < 0.10"
          changeType="positive"
          icon={CheckCircle2}
          description="Within nominal distribution"
        />
        <MetricCard
          title="Moderate Drift"
          value={moderate}
          unit="channels"
          change="0.10 <= PSI < 0.25"
          changeType={moderate > 0 ? 'negative' : 'positive'}
          icon={AlertTriangle}
          description="Early tool wear warning"
        />
        <MetricCard
          title="Critical Drift"
          value={critical}
          unit="channels"
          change={critical > 0 ? 'Retrain triggered' : 'Zero drift breaches'}
          changeType={critical > 0 ? 'negative' : 'positive'}
          icon={ShieldAlert}
          description="PSI >= 0.25 (Trigger Retrain)"
        />
      </div>

      {/* Main Drift Table */}
      <div className="industrial-card p-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Sensor Channel Distribution Shifts</h3>
            <p className="text-xs text-slate-400 font-mono">
              Comparing baseline training distributions vs recent production lots
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Ranked by PSI</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/60">
                <th className="p-2.5">Sensor Channel</th>
                <th className="p-2.5">PSI Score</th>
                <th className="p-2.5">KS Statistic</th>
                <th className="p-2.5">KS P-Value</th>
                <th className="p-2.5">Status</th>
                <th className="p-2.5">Baseline Mean</th>
                <th className="p-2.5">Current Mean</th>
                <th className="p-2.5">Shift (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {(driftData?.top_drifted_sensors || []).map((s) => (
                <tr key={s.sensor} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-2.5 font-semibold text-slate-200">{s.sensor}</td>
                  <td className="p-2.5 font-bold">
                    <span
                      className={
                        s.psi >= 0.25
                          ? 'text-rose-400'
                          : s.psi >= 0.1
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {s.psi.toFixed(4)}
                    </span>
                  </td>
                  <td className="p-2.5 text-slate-300">{s.ks_statistic.toFixed(4)}</td>
                  <td className="p-2.5 text-slate-400">{s.ks_p_value.toFixed(4)}</td>
                  <td className="p-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.status === 'CRITICAL_DRIFT'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : s.status === 'MODERATE_DRIFT'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      }`}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td className="p-2.5 text-slate-400">{s.baseline_mean.toFixed(2)}</td>
                  <td className="p-2.5 text-slate-200">{s.current_mean.toFixed(2)}</td>
                  <td className="p-2.5">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                        <div
                          className={`h-full rounded-full ${
                            s.mean_shift_percent > 10 ? 'bg-rose-500' : 'bg-sky-500'
                          }`}
                          style={{ width: `${Math.min(100, s.mean_shift_percent * 4)}%` }}
                        />
                      </div>
                      <span className="text-slate-300">{s.mean_shift_percent}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Engineering Action Playbook */}
      <div className="industrial-card p-5 border-slate-800 bg-slate-950/60 font-mono">
        <div className="flex items-center space-x-2 mb-3">
          <Wrench className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">Fab Process Engineering Playbook</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded bg-slate-900/60 border border-slate-800/80">
            <span className="text-emerald-400 font-semibold block mb-1">PSI &lt; 0.10: Stable</span>
            <p className="text-slate-400 text-[11px]">
              Chamber operating within calibrated process window. Keep active model in production.
            </p>
          </div>
          <div className="p-3 rounded bg-slate-900/60 border border-slate-800/80">
            <span className="text-amber-400 font-semibold block mb-1">0.10 &le; PSI &lt; 0.25: Moderate</span>
            <p className="text-slate-400 text-[11px]">
              Sensor degradation or minor chamber wall polymer deposition. Schedule clean cycle and monitor closely.
            </p>
          </div>
          <div className="p-3 rounded bg-slate-900/60 border border-slate-800/80">
            <span className="text-rose-400 font-semibold block mb-1">PSI &ge; 0.25: Critical Drift</span>
            <p className="text-slate-400 text-[11px]">
              Major process shift. Trigger retraining pipeline immediately in Pipeline Lab or roll back model.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
