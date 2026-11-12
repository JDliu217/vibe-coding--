async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : '消费端服务暂时不可用');
  }
  return data;
}

export function fetchCampaign() {
  return request('/api/campaign');
}

export function registerPhone(phone) {
  return request('/api/registrations', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export function fetchRegistration(phone) {
  return request(`/api/registrations/${encodeURIComponent(phone)}`);
}
