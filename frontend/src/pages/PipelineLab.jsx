import React, { useState, useEffect } from 'react';
import { GitMerge, Play, Database, CheckCircle2, AlertCircle, RefreshCw, FileText, PlusCircle, ArrowUpRight } from 'lucide-react';
import PipelineVisualizer from '../components/PipelineVisualizer';
import { fetchDatasets, generateSampleBatches, triggerTraining, fetchTrainingJobs, fetchJobStatus, previewDataset } from '../services/api';

export default function PipelineLab({ onModelTrained }) {
  const [datasets, setDatasets] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [activeJob, setActiveJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Training form inputs
  const [targetVersion, setTargetVersion] = useState('');
  const [autoPromote, setAutoPromote] = useState(true);

  const loadData = async () => {
    try {
      const [dList, jList] = await Promise.all([fetchDatasets(), fetchTrainingJobs()]);
      setDatasets(dList);
      setJobs(jList);

      // Check if there is an active running job
      const running = jList.find((j) => j.status === 'running' || j.status === 'queued');
      if (running) {
        setActiveJob(running);
      }
    } catch (e) {
      console.error('Failed to load datasets/jobs', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Poll active job status
  useEffect(() => {
    if (!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const updated = await fetchJobStatus(activeJob.id);
        setActiveJob(updated);
        if (updated.status === 'completed') {
          loadData();
          if (onModelTrained) onModelTrained();
        }
      } catch (e) {
        console.error('Failed polling job', e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJob]);

  const handleTriggerTraining = async () => {
    setLoading(true);
    try {
      const res = await triggerTraining({
        data_dir: 'Training_Batch_Files',
        version: targetVersion || undefined,
        set_active: autoPromote,
      });
      setActiveJob(res);
      setTargetVersion('');
      loadData();
    } catch (e) {
      alert(`Training trigger failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSamples = async () => {
    setGenerating(true);
    try {
      await generateSampleBatches('training', 2, 100);
      await loadData();
    } catch (e) {
      alert(`Sample generation failed: ${e.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handlePreview = async (filename) => {
    try {
      const prev = await previewDataset(filename);
      setPreviewData(prev);
    } catch (e) {
      alert(`Preview failed: ${e.message}`);
    }
  };

  const isRunning = activeJob?.status === 'running' || activeJob?.status === 'queued';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800 gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <span>MLOps Pipeline Orchestration Lab</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
              CLUSTERING + ENSEMBLE
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-mono mt-1">
            Automated schema validation, robust feature scaling, chamber regime clustering, and artifact packaging
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleGenerateSamples}
            disabled={generating}
            className="interactive-btn flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <PlusCircle className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Generating...' : 'Generate New Batches'}</span>
          </button>
          <button
            onClick={loadData}
            className="interactive-btn p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Visual DAG */}
      <PipelineVisualizer
        currentStep={activeJob?.current_step || 'Ready'}
        progressPct={activeJob?.progress_pct || 0}
        isRunning={isRunning}
      />

      {/* Trigger Control Panel & Active Job Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Trigger Controls */}
        <div className="lg:col-span-5 industrial-card p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200">Pipeline Execution Control</h3>
            <span className="text-[10px] font-mono text-slate-500">Autonomous MLOps Trigger</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 font-mono mb-1">Target Model Version (Optional):</label>
              <input
                type="text"
                placeholder="e.g. v20261108_release"
                value={targetVersion}
                onChange={(e) => setTargetVersion(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex items-center space-x-2 pt-1">
              <input
                type="checkbox"
                id="autoPromote"
                checked={autoPromote}
                onChange={(e) => setAutoPromote(e.target.checked)}
                disabled={isRunning}
                className="rounded bg-slate-950 border-slate-700 text-sky-500 focus:ring-0"
              />
              <label htmlFor="autoPromote" className="text-slate-300 font-mono text-xs cursor-pointer">
                Promote to active production model upon completion
              </label>
            </div>

            <div className="pt-2">
              <button
                onClick={handleTriggerTraining}
                disabled={isRunning || loading}
                className="interactive-btn w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-[0_0_15px_rgba(2,132,199,0.3)] disabled:opacity-50"
              >
                <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-pulse' : ''}`} />
                <span>{isRunning ? 'Pipeline Running in Background...' : 'Trigger Full Retraining Pipeline'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Live Step Progress / Job Status Card */}
        <div className="lg:col-span-7 industrial-card p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-slate-200">Execution Progress & Telemetry</h3>
              {activeJob && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {activeJob.id}
                </span>
              )}
            </div>
            {activeJob && (
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                  activeJob.status === 'completed'
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    : activeJob.status === 'running'
                    ? 'bg-amber-950 text-amber-400 border border-amber-800'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {activeJob.status}
              </span>
            )}
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <div className="flex justify-between text-xs font-mono mb-1 text-slate-400">
                <span>Stage: <strong className="text-slate-200">{activeJob?.current_step || 'Idle'}</strong></span>
                <span>{activeJob?.progress_pct || 0}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-sky-500 h-2 rounded-full transition-all duration-300 shadow-[0_0_8px_#0284c7]"
                  style={{ width: `${activeJob?.progress_pct || 0}%` }}
                />
              </div>
            </div>

            {activeJob?.metrics && Object.keys(activeJob.metrics).length > 0 && (
              <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs font-mono">
                <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block">ROC-AUC</span>
                  <strong className="text-emerald-400 text-sm">{activeJob.metrics.roc_auc}</strong>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block">Precision</span>
                  <strong className="text-slate-200 text-sm">{activeJob.metrics.precision}</strong>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block">Recall</span>
                  <strong className="text-slate-200 text-sm">{activeJob.metrics.recall}</strong>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block">F1 Score</span>
                  <strong className="text-sky-400 text-sm">{activeJob.metrics.f1_score}</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ingested Telemetry Batches Table */}
      <div className="industrial-card p-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Raw Telemetry Batches & Schema Contracts</h3>
            <p className="text-xs text-slate-400 font-mono">Ingested sensor files with integrity audit status</p>
          </div>
          <span className="text-xs font-mono text-slate-400">{datasets.length} Batches Tracked</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/60">
                <th className="py-2.5 px-3">Batch Filename</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Wafers</th>
                <th className="py-2.5 px-3">Sensors</th>
                <th className="py-2.5 px-3">Schema Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {datasets.slice(0, 8).map((d) => (
                <tr key={d.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-slate-200">{d.filename}</td>
                  <td className="py-2.5 px-3 uppercase text-[10px] text-slate-400">{d.file_type}</td>
                  <td className="py-2.5 px-3 text-slate-300">{d.row_count}</td>
                  <td className="py-2.5 px-3 text-slate-300">{d.column_count} cols</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                        d.is_valid
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {d.is_valid ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      <span>{d.is_valid ? 'VERIFIED' : 'QUARANTINED'}</span>
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => handlePreview(d.filename)}
                      className="interactive-btn text-xs text-sky-400 hover:text-sky-300 underline font-mono"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0d131f] border border-slate-800 rounded-lg max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-200 text-sm font-mono">{previewData.filename}</h3>
                <p className="text-xs text-slate-400 font-mono">
                  {previewData.row_count} wafers | {previewData.column_count} sensor channels
                </p>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="interactive-btn px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs font-mono hover:bg-slate-700"
              >
                Close
              </button>
            </div>

            <div className="p-4 overflow-auto flex-1 font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    {previewData.columns.slice(0, 10).map((col) => (
                      <th key={col} className="p-2 whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {previewData.preview_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      {previewData.columns.slice(0, 10).map((col) => (
                        <td key={col} className="p-2 whitespace-nowrap text-slate-300">
                          {typeof row[col] === 'number' ? row[col].toFixed(2) : String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
