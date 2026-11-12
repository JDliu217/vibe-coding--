async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : '后端请求失败');
  }
  return data;
}

export function fetchState() {
  return request('/api/state');
}

export function startBatch(body) {
  return request('/api/batches', { method: 'POST', body: JSON.stringify(body) });
}

export function tickBatch(batchId, body) {
  return request(`/api/batches/${batchId}/tick`, { method: 'POST', body: JSON.stringify(body) });
}

export function stopBatch(batchId) {
  return request(`/api/batches/${batchId}/stop`, { method: 'POST' });
}

export function resetLedger() {
  return request('/api/reset', { method: 'POST' });
}
