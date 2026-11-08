/**
 * WaferGuard API Service Client.
 */

const BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? 'https://waferguard.vercel.app' : '');

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

export async function fetchFabOverview() {
  const res = await fetch(`${BASE_URL}/api/v1/monitoring/fab-overview`);
  return res.json();
}

export async function fetchDatasets(fileType = '') {
  const url = fileType ? `${BASE_URL}/api/v1/datasets?file_type=${fileType}` : `${BASE_URL}/api/v1/datasets`;
  const res = await fetch(url);
  return res.json();
}

export async function generateSampleBatches(fileType = 'training', batchCount = 2, samplesPerBatch = 100) {
  const res = await fetch(
    `${BASE_URL}/api/v1/datasets/generate-sample?file_type=${fileType}&batch_count=${batchCount}&samples_per_batch=${samplesPerBatch}`,
    { method: 'POST' }
  );
  return res.json();
}

export async function previewDataset(filename) {
  const res = await fetch(`${BASE_URL}/api/v1/datasets/${filename}/preview`);
  return res.json();
}

export async function triggerTraining(params = {}) {
  const res = await fetch(`${BASE_URL}/api/v1/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return res.json();
}

export async function fetchTrainingJobs() {
  const res = await fetch(`${BASE_URL}/api/v1/train/jobs`);
  return res.json();
}

export async function fetchJobStatus(jobId) {
  const res = await fetch(`${BASE_URL}/api/v1/train/jobs/${jobId}`);
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${BASE_URL}/api/v1/models`);
  return res.json();
}

export async function fetchActiveModel() {
  const res = await fetch(`${BASE_URL}/api/v1/models/active`);
  if (!res.ok) return null;
  return res.json();
}

export async function promoteModel(version) {
  const res = await fetch(`${BASE_URL}/api/v1/models/promote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version }),
  });
  return res.json();
}

export async function rollbackModel() {
  const res = await fetch(`${BASE_URL}/api/v1/models/rollback`, {
    method: 'POST',
  });
  return res.json();
}

export async function predictSingle(payload) {
  const res = await fetch(`${BASE_URL}/api/v1/predict/single`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function predictBatch(filename, modelVersion = null) {
  let url = `${BASE_URL}/api/v1/predict/batch`;
  const params = [];
  if (filename) params.push(`filename=${encodeURIComponent(filename)}`);
  if (modelVersion) params.push(`model_version=${encodeURIComponent(modelVersion)}`);
  if (params.length > 0) url += `?${params.join('&')}`;

  const res = await fetch(url, { method: 'POST' });
  return res.json();
}

export async function fetchDriftReport() {
  const res = await fetch(`${BASE_URL}/api/v1/monitoring/drift`);
  return res.json();
}
