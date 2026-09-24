// Thin wrapper around the DevPulse FastAPI backend.
// Change VITE_API_BASE_URL in a .env file if your backend runs somewhere
// other than the default `uvicorn app.main:app` address.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const TOKEN_KEY = 'devpulse_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, form, auth = true } = {}) {
  const headers = {}
  let payload

  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    payload = new URLSearchParams(body).toString()
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(
      `Could not reach the DevPulse API at ${API_BASE_URL}. Is the FastAPI backend running (uvicorn app.main:app --reload)?`,
      0,
    )
  }

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    const detail = data?.detail
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(', ')
      : detail || `Request failed (${response.status})`
    throw new ApiError(message, response.status)
  }
  return data
}

export const api = {
  // -- auth --
  register: (name, email, password) =>
    request('/auth/register', { method: 'POST', body: { name, email, password }, auth: false }),
  login: (email, password) =>
    request('/auth/login', { method: 'POST', form: true, body: { username: email, password }, auth: false }),
  me: () => request('/auth/me'),
  setLeaderboardOptIn: (leaderboard_opt_in) =>
    request('/auth/leaderboard-preference', { method: 'PATCH', body: { leaderboard_opt_in } }),

  // -- github --
  syncGithub: (username) => request('/github/sync', { method: 'POST', body: { username } }),
  getProfile: () => request('/github/profile'),
  getRepositories: (sortBy = 'stars') => request(`/github/repositories?sort_by=${sortBy}`),

  // -- analytics --
  getOverview: () => request('/analytics/overview'),
  getHistory: (limit = 20) => request(`/analytics/history?limit=${limit}`),
  getLeaderboard: (limit = 20) => request(`/analytics/leaderboard?limit=${limit}`),

  // -- achievements --
  getAchievements: () => request('/achievements'),

  // -- ai --
  careerAnalysis: (target_role) => request('/ai/career-analysis', { method: 'POST', body: { target_role } }),
  resumeBullets: (target_role, tone) =>
    request('/ai/resume-bullets', { method: 'POST', body: { target_role, tone } }),
  getReports: () => request('/ai/reports'),
}
