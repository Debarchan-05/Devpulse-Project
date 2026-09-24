// Mirrors app/services/analytics_service.py::pulse_status on the backend,
// purely for instant, no-network UI coloring — the source of truth for the
// actual label always comes from the API response.
export const PULSE_COLORS = {
  'Peak Pulse': { text: 'text-pulse-400', bg: 'bg-pulse-500/15', ring: 'ring-pulse-500/40' },
  Thriving: { text: 'text-signal-400', bg: 'bg-signal-500/15', ring: 'ring-signal-500/40' },
  'Steady Growth': { text: 'text-rank-400', bg: 'bg-rank-500/15', ring: 'ring-rank-500/40' },
  'Warming Up': { text: 'text-mist-300', bg: 'bg-ink-700', ring: 'ring-ink-600' },
  'Just Getting Started': { text: 'text-mist-500', bg: 'bg-ink-700', ring: 'ring-ink-600' },
}

export function pulseColor(status) {
  return PULSE_COLORS[status] || PULSE_COLORS['Just Getting Started']
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatNumber(n) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n ?? 0)
}

export const PILLAR_LABELS = {
  coding: 'Coding',
  project: 'Project',
  testing: 'Testing',
  documentation: 'Docs',
  activity: 'Activity',
  diversity: 'Diversity',
}
