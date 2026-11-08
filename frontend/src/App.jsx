import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import PipelineLab from './pages/PipelineLab';
import ModelRegistry from './pages/ModelRegistry';
import Inference from './pages/Inference';
import Monitoring from './pages/Monitoring';
import { fetchActiveModel } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeModel, setActiveModel] = useState(null);
  const [liveTelemetry, setLiveTelemetry] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  const loadActiveModel = async () => {
    try {
      const model = await fetchActiveModel();
      setActiveModel(model);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadActiveModel();

    // Setup live telemetry: WebSocket for local dev, responsive streaming simulator for GitHub Pages
    let ws;
    let intervalId;

    const startFallback = () => {
      setIsConnected(true);
      const chambers = ['Chamber_A (CMP)', 'Chamber_B (Litho)', 'Chamber_C (Etch)'];
      intervalId = setInterval(() => {
        const isAnomaly = Math.random() < 0.05;
        const now = new Date();
        const waferId = `W-${now.toTimeString().split(' ')[0].replace(/:/g, '')}-${Math.floor(Math.random() * 900 + 100)}`;
        setLiveTelemetry({
          timestamp: now.toISOString(),
          wafer_id: waferId,
          chamber: chambers[Math.floor(Math.random() * chambers.length)],
          status: isAnomaly ? 'ANOMALY' : 'NORMAL',
          sensors: {
            rf_power_kw: (13.56 + (isAnomaly ? (Math.random() * 4 - 2) : (Math.random() * 0.4 - 0.2))).toFixed(2),
            chamber_temp_c: (65.0 + (isAnomaly ? (Math.random() * 15 - 7) : (Math.random() * 1.5 - 0.7))).toFixed(1),
            pressure_mtorr: (15.2 + (isAnomaly ? (Math.random() * 5 - 2.5) : (Math.random() * 0.5 - 0.25))).toFixed(2),
            vibration_g: (0.12 + (isAnomaly ? 0.15 : 0.01)).toFixed(3),
            gas_flow_sccm: (240.0 + (Math.random() * 6 - 3)).toFixed(1),
          },
          alarm: isAnomaly ? 'High RF Power Deviation' : null,
        });
      }, 2200);
    };

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

      try {
        ws = new WebSocket(wsUrl);
        ws.onopen = () => setIsConnected(true);
        ws.onmessage = (event) => {
          try {
            setLiveTelemetry(JSON.parse(event.data));
          } catch (e) {
            console.error(e);
          }
        };
        ws.onclose = () => {
          setIsConnected(false);
          startFallback();
        };
        ws.onerror = () => {
          setIsConnected(false);
          startFallback();
        };
      } catch {
        startFallback();
      }
    } else {
      startFallback();
    }

    return () => {
      if (ws) ws.close();
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#080c14] text-slate-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeModel={activeModel}
        isConnected={isConnected}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && <Dashboard liveTelemetry={liveTelemetry} />}
        {activeTab === 'pipeline' && <PipelineLab onModelTrained={loadActiveModel} />}
        {activeTab === 'models' && <ModelRegistry />}
        {activeTab === 'inference' && <Inference />}
        {activeTab === 'monitoring' && <Monitoring />}
      </main>

      <footer className="border-t border-slate-900 bg-[#060910] py-4 text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>WaferGuard MLOps Platform &copy; {new Date().getFullYear()}</span>
          <span>Industrial Telemetry &bull; K-Means Chamber Ensembles &bull; Real-Time Diagnostics</span>
        </div>
      </footer>
    </div>
  );
}
