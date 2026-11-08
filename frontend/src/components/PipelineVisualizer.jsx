import React, { useState } from 'react';
import { Database, ShieldCheck, Filter, Cpu, Layers, Archive, ArrowRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function PipelineVisualizer({ currentStep, progressPct, isRunning }) {
  const [selectedNode, setSelectedNode] = useState(null);

  const stages = [
    {
      id: 'ingestion',
      name: 'Batch Ingestion',
      icon: Database,
      desc: 'Ingests raw multi-sensor telemetry batches from fabrication chambers',
      details: 'Supports .csv and DVC-backed batches. Reads sensor telemetry channels (Sensor_1 to Sensor_N) and historical quality markers.',
      output: 'Raw batch dataframes',
      status: progressPct >= 15 ? 'completed' : isRunning ? 'running' : 'idle',
    },
    {
      id: 'validation',
      name: 'Schema Validation',
      icon: ShieldCheck,
      desc: 'Validates primary key syntax, missing value bounds, and dead sensor anomalies',
      details: 'Enforces strict data contracts: Wafer identifier existence, target value consistency, and automatic quarantine routing for malformed lots.',
      output: 'Clean raw batches + Quarantine reports',
      status: progressPct >= 30 ? 'completed' : progressPct >= 15 ? 'running' : 'idle',
    },
    {
      id: 'preprocessing',
      name: 'Robust Feature Prep',
      icon: Filter,
      desc: 'Null imputation, zero-variance pruning, and outlier-resistant scaling',
      details: 'Prunes sensor columns with >35% missing telemetry or zero variance. Imputes remaining via median strategy and standardizes via RobustScaler.',
      output: 'Scaled feature matrix X + Baseline statistics',
      status: progressPct >= 60 ? 'completed' : progressPct >= 30 ? 'running' : 'idle',
    },
    {
      id: 'clustering',
      name: 'Chamber Clustering',
      icon: Cpu,
      desc: 'K-Means clustering to partition operational chamber variations',
      details: 'Optimizes cluster count K (2 to 4) using Silhouette analysis. Partitions CMP tool wear and plasma etch baseline regimes.',
      output: 'Optimal K clusters + Cluster assignments',
      status: progressPct >= 80 ? 'completed' : progressPct >= 60 ? 'running' : 'idle',
    },
    {
      id: 'ensemble',
      name: 'Clustered Ensembles',
      icon: Layers,
      desc: 'Cluster-specific ensemble classifiers with class-balanced weighting',
      details: 'Trains specialized Random Forest and HistGradientBoosting classifiers per cluster. Handles severe class imbalance and edge-case single classes.',
      output: 'Cluster models + ROC-AUC & Confusion Matrix',
      status: progressPct >= 95 ? 'completed' : progressPct >= 80 ? 'running' : 'idle',
    },
    {
      id: 'registry',
      name: 'Model Registry',
      icon: Archive,
      desc: 'Versioned artifact packaging, metadata ledger, and production promotion',
      details: 'Serializes preprocessor, clusterer, and ensemble models into versioned artifacts with complete metadata card and zero-downtime rollback pointer.',
      output: 'Production model bundle (active_model.json)',
      status: progressPct === 100 ? 'completed' : progressPct >= 95 ? 'running' : 'idle',
    },
  ];

  const activeNode = selectedNode || stages[0];

  return (
    <div className="industrial-card p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">MLOps Pipeline Architecture Topology</h3>
          <p className="text-xs text-slate-400 font-mono">End-to-End Clustered Ensemble Training DAG</p>
        </div>
        {isRunning && (
          <div className="flex items-center space-x-2 px-3 py-1 rounded bg-sky-950 border border-sky-800 text-xs font-mono text-sky-300">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
            <span>{currentStep} ({progressPct}%)</span>
          </div>
        )}
      </div>

      {/* DAG Flow Nodes */}
      <div className="py-6 overflow-x-auto">
        <div className="flex items-center min-w-[700px] justify-between">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;
            const isSelected = activeNode.id === stage.id;
            const isCompleted = stage.status === 'completed';
            const isCurrentRunning = stage.status === 'running';

            return (
              <React.Fragment key={stage.id}>
                {/* Stage Node Button */}
                <button
                  onClick={() => setSelectedNode(stage)}
                  className={`interactive-btn flex flex-col items-center p-3 rounded-lg border text-center w-28 transition-all ${
                    isSelected
                      ? 'border-sky-500 bg-sky-950/40 shadow-[0_0_15px_rgba(2,132,199,0.2)]'
                      : isCurrentRunning
                      ? 'border-amber-500 bg-amber-950/30 animate-pulse'
                      : isCompleted
                      ? 'border-emerald-600/60 bg-emerald-950/20'
                      : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div
                    className={`w-9 h-9 rounded-md flex items-center justify-center mb-2 ${
                      isCompleted
                        ? 'bg-emerald-900/60 text-emerald-400'
                        : isCurrentRunning
                        ? 'bg-amber-900/60 text-amber-400'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[11px] font-semibold text-slate-200 leading-tight mb-1">
                    {stage.name}
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase ${
                      isCompleted
                        ? 'bg-emerald-900/50 text-emerald-300'
                        : isCurrentRunning
                        ? 'bg-amber-900/50 text-amber-300'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {stage.status}
                  </span>
                </button>

                {/* Arrow Connector */}
                {idx < stages.length - 1 && (
                  <div className="flex-1 px-1 flex items-center justify-center text-slate-600">
                    <ArrowRight className="w-4 h-4" />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Selected Node Inspector Drawer */}
      <div className="p-4 rounded-md bg-slate-900/80 border border-slate-800/80 text-xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-sky-400 text-sm">{activeNode.name}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              Stage {stages.findIndex((s) => s.id === activeNode.id) + 1} of 6
            </span>
          </div>
          <span className="font-mono text-slate-400">Artifact: <strong className="text-slate-200">{activeNode.output}</strong></span>
        </div>
        <p className="text-slate-300 mb-2">{activeNode.desc}</p>
        <p className="text-slate-400 font-mono text-[11px] bg-slate-950 p-2.5 rounded border border-slate-800/60">
          {activeNode.details}
        </p>
      </div>
    </div>
  );
}
