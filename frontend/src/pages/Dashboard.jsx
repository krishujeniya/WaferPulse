import React, { useState, useEffect } from 'react';
import { Activity, Cpu, AlertTriangle, CheckCircle2, RefreshCw, Radio, Gauge, Zap } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import WaferMap from '../components/WaferMap';
import { fetchFabOverview } from '../services/api';

export default function Dashboard({ liveTelemetry }) {
  const [fabData, setFabData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDie, setSelectedDie] = useState(null);

  const loadData = async () => {
    try {
      const data = await fetchFabOverview();
      setFabData(data);
    } catch (e) {
      console.error('Failed to load fab overview', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const yieldRate = fabData?.overall_yield_rate;
  const totalWafers = fabData?.total_wafers_processed;
  const alarmCount = fabData?.active_alarms_count;
  const systemState = alarmCount == null ? 'UNAVAILABLE' : alarmCount > 0 ? 'ATTENTION' : 'NOMINAL';

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800 gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <span>Fab operations</span>
            <span className={`state-badge state-${systemState.toLowerCase()}`}>
              {systemState}
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-mono mt-1">
            Chamber telemetry, wafer yield, and sensor alerts
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            className="interactive-btn flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Yield Rate"
          value={yieldRate ?? '—'}
          unit="%"
          change={fabData ? 'Live overview' : 'Waiting for API'}
          changeType={fabData ? 'positive' : 'neutral'}
          icon={CheckCircle2}
          description="Standard spec >= 95%"
        />
        <MetricCard
          title="Wafers Inspected"
          value={totalWafers?.toLocaleString() ?? '—'}
          unit="wafers"
          change={fabData ? `${fabData.chambers?.length ?? 0} chambers` : 'Waiting for API'}
          changeType="neutral"
          icon={Cpu}
          description="CMP, Litho, Plasma Etch"
        />
        <MetricCard
          title="Defect Anomaly Rate"
          value={yieldRate == null ? '—' : (100 - yieldRate).toFixed(2)}
          unit="%"
          change="Clustered Ensemble"
          changeType={yieldRate == null ? 'neutral' : yieldRate < 95 ? 'negative' : 'positive'}
          icon={Activity}
          description="Target < 5.0%"
        />
        <MetricCard
          title="Critical Sensor Alarms"
          value={alarmCount ?? '—'}
          unit="channels"
          change={alarmCount == null ? 'Waiting for API' : alarmCount === 0 ? 'Within spec' : 'Review alerts'}
          changeType={alarmCount == null ? 'neutral' : alarmCount === 0 ? 'positive' : 'negative'}
          icon={AlertTriangle}
          description="KS & PSI distribution drift"
        />
      </div>

      {/* Main Dual Grid: Wafer Map & Live Chamber Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 300mm Silicon Wafer Map */}
        <div className="lg:col-span-6">
          <WaferMap onSelectDie={setSelectedDie} />
        </div>

        {/* Right: Chamber Status Matrix & Live Pulse */}
        <div className="lg:col-span-6 space-y-4">
          <div className="industrial-card p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Chamber Operating Regimes</h3>
                <p className="text-xs text-slate-400 font-mono">Real-time pressure, RF power, and temperature</p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                K-Means Clustered
              </span>
            </div>

            <div className="mt-4 space-y-3">
              {(fabData?.chambers || []).map((ch) => (
                <div key={ch.chamber_id} className="p-3.5 rounded-lg bg-slate-900/70 border border-slate-800/80">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-slate-200">{ch.chamber_id}</span>
                      <span className="text-[10px] font-mono text-slate-400">({ch.active_recipe})</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                        ch.status === 'OPTIMAL'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {ch.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono pt-1">
                    <div className="p-1.5 rounded bg-slate-950 border border-slate-800/50">
                      <span className="text-[10px] text-slate-500 block">Yield</span>
                      <strong className="text-emerald-400">{ch.yield_rate}%</strong>
                    </div>
                    <div className="p-1.5 rounded bg-slate-950 border border-slate-800/50">
                      <span className="text-[10px] text-slate-500 block">RF Power</span>
                      <strong className="text-slate-200">{ch.rf_power_kw} kW</strong>
                    </div>
                    <div className="p-1.5 rounded bg-slate-950 border border-slate-800/50">
                      <span className="text-[10px] text-slate-500 block">Pressure</span>
                      <strong className="text-slate-200">{ch.pressure_mtorr} mTorr</strong>
                    </div>
                    <div className="p-1.5 rounded bg-slate-950 border border-slate-800/50">
                      <span className="text-[10px] text-slate-500 block">Temp</span>
                      <strong className="text-slate-200">{ch.temp_celsius} °C</strong>
                    </div>
                  </div>
                </div>
              ))}
              {!loading && !fabData && <p className="state-message" role="status">Fab overview is unavailable. Check the API connection and refresh.</p>}
              {fabData?.chambers?.length === 0 && <p className="state-message">No chamber data is available.</p>}
            </div>
          </div>

          {/* Live WebSocket Telemetry Pulse */}
          <div className="industrial-card p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Radio className="w-4 h-4 text-sky-400 animate-pulse" />
                <h3 className="text-sm font-semibold text-slate-200">Live Telemetry Pulse Feed</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-500">WebSocket /ws/telemetry</span>
            </div>

            <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs space-y-2">
              {liveTelemetry ? (
                <>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Wafer: <strong className="text-sky-400">{liveTelemetry.wafer_id}</strong></span>
                    <span>Chamber: <strong className="text-slate-200">{liveTelemetry.chamber}</strong></span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        liveTelemetry.status === 'NORMAL'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {liveTelemetry.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-center text-[11px] pt-1 border-t border-slate-900 text-slate-300">
                    <div>RF: {liveTelemetry.sensors.rf_power_kw} kW</div>
                    <div>Temp: {liveTelemetry.sensors.chamber_temp_c} °C</div>
                    <div>Press: {liveTelemetry.sensors.pressure_mtorr} mTorr</div>
                    <div>Vib: {liveTelemetry.sensors.vibration_g} g</div>
                  </div>
                </>
              ) : (
                <div className="py-2 text-center text-slate-500 text-xs">
                  Streaming incoming sensor telemetry packets from fab chambers...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
