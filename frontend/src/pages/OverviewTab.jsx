import { useEffect, useState } from 'react'
import { TrendingDown, TrendingUp } from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { Card, ErrorNote, Loader } from '../components/ui'
import SyncForm from '../components/SyncForm'
import { useToast } from '../context/ToastContext'
import { formatDate, formatNumber, pulseColor } from '../lib/pulse'

export default function OverviewTab() {
  const { push } = useToast()
  const [loading, setLoading] = useState(true)
  const [needsSync, setNeedsSync] = useState(false)
  const [error, setError] = useState('')
  const [overview, setOverview] = useState(null)
  const [history, setHistory] = useState([])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [overviewData, historyData] = await Promise.all([api.getOverview(), api.getHistory(30)])
      setOverview(overviewData)
      setHistory(historyData)
      setNeedsSync(false)
    } catch (err) {
      if (err.status === 400) {
        setNeedsSync(true)
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleSynced = (result) => {
    push(`Synced @${result.profile.github_username} — Pulse Score ${Math.round(result.scores.overall)}`, 'success')
    result.new_badges?.forEach((badge) => {
      push(`${badge.icon} Badge unlocked: ${badge.name}`, 'success', 6000)
    })
    load()
  }

  if (loading) return <Loader label="Reading vitals…" />

  if (needsSync) {
    return (
      <div>
        <PageHeader title="Overview" subtitle="No profile synced yet." />
        <SyncForm onSynced={handleSynced} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="Overview" subtitle="Something went wrong." />
        <ErrorNote message={error} />
        <SyncForm onSynced={handleSynced} />
      </div>
    )
  }

  const colors = pulseColor(overview.pulse_status)
  const radarData = Object.entries(overview.metrics)
    .filter(([key]) => key !== 'overall')
    .map(([key, value]) => ({ pillar: key.charAt(0).toUpperCase() + key.slice(1), value }))

  const chartData = history.map((h) => ({ date: formatDate(h.created_at), score: h.overall }))
  const languages = Object.entries(overview.top_languages).slice(0, 6)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader title="Overview" subtitle="Your developer vitals, at a glance." />
        <SyncForm compact onSynced={handleSynced} />
      </div>

      {/* Hero score */}
      <Card className="flex flex-col items-start gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-mist-500">Pulse Score</p>
          <div className="mt-1 flex items-baseline gap-3">
            <span className="font-mono text-5xl font-semibold text-mist-100">
              {Math.round(overview.developer_score)}
            </span>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ${colors.bg} ${colors.text} ${colors.ring}`}>
              {overview.pulse_status}
            </span>
          </div>
          {overview.score_change !== null && overview.score_change !== undefined && (
            <p
              className={`mt-2 flex items-center gap-1 text-xs font-medium ${
                overview.score_change >= 0 ? 'text-signal-400' : 'text-pulse-400'
              }`}
            >
              {overview.score_change >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
              {overview.score_change >= 0 ? '+' : ''}
              {overview.score_change} since last sync
            </p>
          )}
        </div>

        <div className="flex gap-8">
          <Stat label="Repositories" value={formatNumber(overview.total_repositories)} />
          <Stat label="Total stars" value={formatNumber(overview.total_stars)} />
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Radar of 6 pillars */}
        <Card className="p-6 lg:col-span-2">
          <h3 className="mb-4 font-display text-sm font-semibold text-mist-100">Score breakdown</h3>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} outerRadius="75%">
              <PolarGrid stroke="var(--color-ink-600)" />
              <PolarAngleAxis dataKey="pillar" tick={{ fill: 'var(--color-mist-500)', fontSize: 11 }} />
              <Radar dataKey="value" stroke="var(--color-pulse-500)" fill="var(--color-pulse-500)" fillOpacity={0.28} />
              <Tooltip
                contentStyle={{
                  background: 'var(--color-ink-800)',
                  border: '1px solid var(--color-ink-600)',
                  borderRadius: 10,
                  fontSize: 12,
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </Card>

        {/* History line chart */}
        <Card className="p-6 lg:col-span-3">
          <h3 className="mb-4 font-display text-sm font-semibold text-mist-100">Growth over time</h3>
          {chartData.length > 1 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="pulseFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-pulse-500)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--color-pulse-500)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--color-ink-700)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: 'var(--color-mist-500)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--color-mist-500)', fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--color-ink-800)',
                    border: '1px solid var(--color-ink-600)',
                    borderRadius: 10,
                    fontSize: 12,
                  }}
                />
                <Area type="monotone" dataKey="score" stroke="var(--color-pulse-500)" strokeWidth={2.5} fill="url(#pulseFill)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[240px] flex-col items-center justify-center gap-2 text-center text-sm text-mist-500">
              <p>Sync again after making changes on GitHub</p>
              <p>to start seeing a growth trend here.</p>
            </div>
          )}
        </Card>
      </div>

      {/* Top languages */}
      {languages.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-4 font-display text-sm font-semibold text-mist-100">Top languages</h3>
          <div className="flex flex-wrap gap-2">
            {languages.map(([lang, count]) => (
              <span
                key={lang}
                className="rounded-full border border-ink-600 bg-ink-900 px-3 py-1.5 font-mono text-xs text-mist-300"
              >
                {lang} <span className="text-mist-500">· {count}</span>
              </span>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export function PageHeader({ title, subtitle }) {
  return (
    <div>
      <h2 className="font-display text-xl font-bold text-mist-100">{title}</h2>
      {subtitle && <p className="mt-0.5 text-sm text-mist-500">{subtitle}</p>}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-mist-500">{label}</p>
      <p className="mt-1 font-mono text-2xl text-mist-100">{value}</p>
    </div>
  )
}
