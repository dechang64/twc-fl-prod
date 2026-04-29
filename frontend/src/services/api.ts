const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const api = {
  health: () => fetch(`${API_BASE.replace('/api', '')}/api/health`).then(r => r.json()),
  formulations: () => fetch(`${API_BASE}/formulations`).then(r => r.json()),
  createFormulation: (data: object) => fetch(`${API_BASE}/formulations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  predict: (data: object) => fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  optimize: (n_trials?: number) => fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n_trials: n_trials || 60 }),
  }).then(r => r.json()),
  flStatus: () => fetch(`${API_BASE}/fl/status`).then(r => r.json()),
  flRun: (n_rounds?: number) => fetch(`${API_BASE}/fl/rounds`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n_rounds: n_rounds || 5 }),
  }).then(r => r.json()),
}
