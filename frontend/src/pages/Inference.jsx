import React, { useState, useEffect } from 'react';
import { Cpu, FileText, CheckCircle2, AlertTriangle, ArrowRight, Play, Download, Search, Sliders } from 'lucide-react';
import { fetchActiveModel, predictSingle, predictBatch, fetchDatasets } from '../services/api';

export default function Inference() {
  const [activeTab, setActiveTab] = useState('single'); // 'single' or 'batch'
  const [activeModel, setActiveModel] = useState(null);

  // Single wafer state
  const [waferId, setWaferId] = useState('Wafer_20261108_Live_001');
  const [sensorValues, setSensorValues] = useState({});
  const [singleResult, setSingleResult] = useState(null);
  const [singleLoading, setSingleLoading] = useState(false);

  // Batch state
  const [batchFiles, setBatchFiles] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState('');
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [filterMode, setFilterMode] = useState('all'); // all, defect, pass
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function init() {
      try {
        const [model, datasets] = await Promise.all([
          fetchActiveModel(),
          fetchDatasets('prediction'),
        ]);
        setActiveModel(model);
        setBatchFiles(datasets);
        if (datasets.length > 0) {
          setSelectedBatch(datasets[0].filename);
        }

        // Initialize default sensor values
        if (model?.feature_columns) {
          const initVals = {};
          model.feature_columns.forEach((f) => {
            initVals[f] = 100.0;
          });
          setSensorValues(initVals);
        }
      } catch (e) {
        console.error(e);
      }
    }
    init();
  }, []);

  const handleApplyPreset = (presetType) => {
    if (!activeModel?.feature_columns) return;
    const base = {};
    activeModel.feature_columns.forEach((f) => {
      base[f] = 100.0;
    });

    if (presetType === 'nominal') {
      setWaferId(`Wafer_Nominal_${Math.floor(Math.random() * 900 + 100)}`);
      setSensorValues(base);
    } else if (presetType === 'rf_fault') {
      setWaferId(`Wafer_RF_Fault_${Math.floor(Math.random() * 900 + 100)}`);
      // Inject heavy RF bias shift on Sensor_11 & Sensor_25
      base['Sensor_11'] = 148.5;
      base['Sensor_25'] = 135.2;
      setSensorValues(base);
    } else if (presetType === 'pressure_fault') {
      setWaferId(`Wafer_Pressure_Fault_${Math.floor(Math.random() * 900 + 100)}`);
      base['Sensor_25'] = 45.0; // severe low pressure drop
      base['Sensor_42'] = 160.0;
      setSensorValues(base);
    }
  };

  const handleSinglePredict = async () => {
    setSingleLoading(true);
    try {
      const res = await predictSingle({
        wafer_id: waferId,
        sensors: sensorValues,
      });
      setSingleResult(res);
    } catch (e) {
      alert(`Single prediction failed: ${e.message}`);
    } finally {
      setSingleLoading(false);
    }
  };

  const handleBatchPredict = async () => {
    setBatchLoading(true);
    try {
      const res = await predictBatch(selectedBatch);
      setBatchResult(res);
    } catch (e) {
      alert(`Batch prediction failed: ${e.message}`);
    } finally {
      setBatchLoading(false);
    }
  };

  const filteredBatchResults = (batchResult?.results || []).filter((r) => {
    if (filterMode === 'defect' && !r.is_defective) return false;
    if (filterMode === 'pass' && r.is_defective) return false;
    if (searchQuery && !r.wafer_id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800 gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <span>Inference & Root Cause Diagnosis</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
              REAL-TIME & BATCH
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-mono mt-1">
            Run chamber cluster inference and isolate top anomalous sensors causing wafer deviations
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-md bg-slate-900 p-1 border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-3 py-1.5 rounded transition-all ${
              activeTab === 'single'
                ? 'bg-sky-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Single Wafer Simulator
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={`px-3 py-1.5 rounded transition-all ${
              activeTab === 'batch'
                ? 'bg-sky-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Batch CSV Prediction
          </button>
        </div>
      </div>

      {activeTab === 'single' ? (
        /* Single Wafer Simulation Tab */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls & Presets */}
          <div className="lg:col-span-5 industrial-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200">Wafer Telemetry Injection</h3>
              <span className="text-[10px] font-mono text-slate-500">Live Simulator</span>
            </div>

            <div>
              <label className="block text-slate-400 font-mono text-xs mb-1">Wafer Serial Identifier:</label>
              <input
                type="text"
                value={waferId}
                onChange={(e) => setWaferId(e.target.value)}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500"
              />
            </div>

            {/* Quick Presets */}
            <div>
              <label className="block text-slate-400 font-mono text-xs mb-1.5">Simulation Presets:</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleApplyPreset('nominal')}
                  className="interactive-btn p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:border-emerald-700 text-[11px] font-mono text-center"
                >
                  Nominal (Pass)
                </button>
                <button
                  onClick={() => handleApplyPreset('rf_fault')}
                  className="interactive-btn p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:border-rose-700 text-[11px] font-mono text-center"
                >
                  RF Power Fault
                </button>
                <button
                  onClick={() => handleApplyPreset('pressure_fault')}
                  className="interactive-btn p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:border-amber-700 text-[11px] font-mono text-center"
                >
                  Pressure Drop
                </button>
              </div>
            </div>

            {/* Critical Sensor Adjusters */}
            <div className="pt-2 border-t border-slate-800 space-y-3 font-mono text-xs">
              <span className="text-slate-400 block font-semibold">Tweak Sensor Deviations:</span>
              {['Sensor_11', 'Sensor_25', 'Sensor_42'].map((sensor) => (
                <div key={sensor} className="space-y-1">
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>{sensor}:</span>
                    <span className="text-sky-400 font-bold">{sensorValues[sensor] ?? 100}</span>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="200"
                    step="0.5"
                    value={sensorValues[sensor] ?? 100}
                    onChange={(e) =>
                      setSensorValues({ ...sensorValues, [sensor]: parseFloat(e.target.value) })
                    }
                    className="w-full accent-sky-500 cursor-pointer"
                  />
                </div>
              ))}
            </div>

            <div className="pt-2">
              <button
                onClick={handleSinglePredict}
                disabled={singleLoading}
                className="interactive-btn w-full py-2.5 px-4 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-[0_0_15px_rgba(2,132,199,0.3)] flex items-center justify-center space-x-2"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{singleLoading ? 'Running Ensemble Inference...' : 'Execute Wafer Diagnosis'}</span>
              </button>
            </div>
          </div>

          {/* Diagnosis & Root Cause Result */}
          <div className="lg:col-span-7 industrial-card p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200">Defect Classification & Root-Cause Attribution</h3>
              <span className="text-[10px] font-mono text-slate-500">Z-Score Sensor Analysis</span>
            </div>

            {singleResult ? (
              <div className="mt-4 space-y-4">
                {/* Result Status Banner */}
                <div
                  className={`p-4 rounded-lg border flex items-center justify-between font-mono ${
                    singleResult.is_defective
                      ? 'bg-rose-950/30 border-rose-800/80 text-rose-300'
                      : 'bg-emerald-950/30 border-emerald-800/80 text-emerald-300'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        singleResult.is_defective
                          ? 'bg-rose-900/60 text-rose-400 shadow-[0_0_12px_#f43f5e]'
                          : 'bg-emerald-900/60 text-emerald-400 shadow-[0_0_12px_#10b981]'
                      }`}
                    >
                      {singleResult.is_defective ? (
                        <AlertTriangle className="w-5 h-5" />
                      ) : (
                        <CheckCircle2 className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <span className="text-xs text-slate-400 block">{singleResult.wafer_id}</span>
                      <strong className="text-base uppercase tracking-wider">{singleResult.prediction}</strong>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Defect Probability</span>
                    <strong className="text-xl font-bold">
                      {(singleResult.defect_probability * 100).toFixed(1)}%
                    </strong>
                  </div>
                </div>

                {/* Root Cause Attribution Table */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 font-mono mb-2">
                    Top Contributing Sensor Deviations:
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left font-mono text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/40">
                          <th className="p-2">Sensor Channel</th>
                          <th className="p-2">Actual Value</th>
                          <th className="p-2">Baseline Mean</th>
                          <th className="p-2">Z-Score Deviation</th>
                          <th className="p-2">Severity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/50">
                        {singleResult.top_anomalies.map((a) => (
                          <tr key={a.sensor} className="hover:bg-slate-900/30">
                            <td className="p-2 font-semibold text-slate-200">{a.sensor}</td>
                            <td className="p-2 text-slate-300">{a.value.toFixed(1)}</td>
                            <td className="p-2 text-slate-400">{a.baseline_mean.toFixed(1)}</td>
                            <td className="p-2 font-bold">
                              <span
                                className={
                                  Math.abs(a.z_score) >= 3
                                    ? 'text-rose-400'
                                    : Math.abs(a.z_score) >= 2
                                    ? 'text-amber-400'
                                    : 'text-slate-300'
                                }
                              >
                                {a.z_score > 0 ? `+${a.z_score}` : a.z_score} σ ({a.direction})
                              </span>
                            </td>
                            <td className="p-2">
                              <span
                                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                  a.severity === 'CRITICAL'
                                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                    : a.severity === 'WARNING'
                                    ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {a.severity}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 font-mono text-xs">
                Select a preset or adjust sensor sliders and click Execute Wafer Diagnosis to inspect
                model classifications and root-cause attributions.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Batch CSV Inference Tab */
        <div className="space-y-6">
          <div className="industrial-card p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Batch Inference Pipeline</h3>
                <p className="text-xs text-slate-400 font-mono">Execute high-throughput scoring on complete manufacturing runs</p>
              </div>

              <div className="flex items-center space-x-2">
                <select
                  value={selectedBatch}
                  onChange={(e) => setSelectedBatch(e.target.value)}
                  className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none"
                >
                  {batchFiles.map((b) => (
                    <option key={b.filename} value={b.filename}>
                      {b.filename} ({b.row_count} wafers)
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleBatchPredict}
                  disabled={batchLoading}
                  className="interactive-btn px-4 py-1.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs font-mono shadow-[0_0_12px_rgba(2,132,199,0.3)] disabled:opacity-50 flex items-center space-x-1.5"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{batchLoading ? 'Scoring...' : 'Score Batch'}</span>
                </button>
              </div>
            </div>

            {batchResult && (
              <div className="mt-4 space-y-4">
                {/* Batch Metrics Header */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-center">
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Total Wafers Scored</span>
                    <strong className="text-xl text-slate-100">{batchResult.total_wafers}</strong>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Defects Intercepted</span>
                    <strong className="text-xl text-rose-400">{batchResult.defects_count}</strong>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Lot Yield Rate</span>
                    <strong className="text-xl text-emerald-400">{batchResult.yield_rate}%</strong>
                  </div>
                </div>

                {/* Filter and Search Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 font-mono text-xs">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setFilterMode('all')}
                      className={`px-2.5 py-1 rounded ${
                        filterMode === 'all' ? 'bg-slate-800 text-sky-400 font-bold' : 'text-slate-400'
                      }`}
                    >
                      All ({batchResult.results.length})
                    </button>
                    <button
                      onClick={() => setFilterMode('defect')}
                      className={`px-2.5 py-1 rounded ${
                        filterMode === 'defect' ? 'bg-rose-950 text-rose-400 font-bold border border-rose-800' : 'text-slate-400'
                      }`}
                    >
                      Defects Only ({batchResult.defects_count})
                    </button>
                    <button
                      onClick={() => setFilterMode('pass')}
                      className={`px-2.5 py-1 rounded ${
                        filterMode === 'pass' ? 'bg-emerald-950 text-emerald-400 font-bold border border-emerald-800' : 'text-slate-400'
                      }`}
                    >
                      Pass Only ({batchResult.total_wafers - batchResult.defects_count})
                    </button>
                  </div>

                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search wafer serial..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 pr-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                    />
                  </div>
                </div>

                {/* Results Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/60">
                        <th className="p-2.5">Wafer Serial</th>
                        <th className="p-2.5">Cluster</th>
                        <th className="p-2.5">Verdict</th>
                        <th className="p-2.5">Defect Probability</th>
                        <th className="p-2.5">Top Anomalous Sensor Attribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {filteredBatchResults.map((r) => (
                        <tr key={r.wafer_id} className="hover:bg-slate-900/40">
                          <td className="p-2.5 font-semibold text-slate-200">{r.wafer_id}</td>
                          <td className="p-2.5 text-slate-400">Cluster {r.cluster_id}</td>
                          <td className="p-2.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                r.is_defective
                                  ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                  : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              }`}
                            >
                              {r.prediction}
                            </span>
                          </td>
                          <td className="p-2.5 text-slate-300">
                            {(r.defect_probability * 100).toFixed(1)}%
                          </td>
                          <td className="p-2.5 text-slate-400 text-[11px]">
                            {r.top_anomalous_sensors || 'Normal Operating Window'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
