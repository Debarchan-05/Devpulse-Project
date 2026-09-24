import { useEffect, useState } from 'react'
import { Trophy } from 'lucide-react'
import { api } from '../api/client'
import { Card, EmptyState, ErrorNote, Loader } from '../components/ui'
import { PageHeader } from './OverviewTab'
import { useAuth } from '../context/AuthContext'

const RANK_STYLES = {
  1: 'text-signal-400 border-signal-500/40 bg-signal-500/10',
  2: 'text-mist-100 border-ink-500 bg-ink-700',
  3: 'text-pulse-400 border-pulse-500/30 bg-pulse-500/10',
}

export default function LeaderboardTab() {
  const { user, refreshUser } = useAuth()
  const [board, setBoard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(false)

  const load = () => {
    setLoading(true)
    api
      .getLeaderboard(20)
      .then(setBoard)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const toggleOptIn = async () => {
    setUpdating(true)
    try {
      await api.setLeaderboardOptIn(!user.leaderboard_opt_in)
      await refreshUser()
      load()
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader title="Leaderboard" subtitle="Ranked live with SQL window functions, not sorted in JavaScript." />
        <button
          onClick={toggleOptIn}
          disabled={updating}
          className="rounded-xl border border-ink-600 px-3 py-2 text-xs font-medium text-mist-300 transition hover:border-pulse-500/50 hover:text-pulse-400 disabled:opacity-50"
        >
          {user?.leaderboard_opt_in ? 'Visible on leaderboard — opt out' : 'Hidden from leaderboard — opt in'}
        </button>
      </div>

      {error && <ErrorNote message={error} />}
      {loading ? (
        <Loader label="Ranking developers…" />
      ) : board.entries.length === 0 ? (
        <EmptyState icon={Trophy} title="No rankings yet" description="Sync a GitHub profile to appear on the leaderboard." />
      ) : (
        <Card className="overflow-hidden">
          {board.your_rank && (
            <div className="border-b border-ink-700 bg-ink-900/60 px-5 py-2.5 text-xs text-mist-500">
              Your current rank: <span className="font-mono text-mist-100">#{board.your_rank}</span>
            </div>
          )}
          <ul>
            {board.entries.map((entry) => (
              <li
                key={entry.rank}
                className={`flex items-center gap-4 border-b border-ink-700/60 px-5 py-3.5 last:border-0 ${
                  entry.is_you ? 'bg-pulse-500/5' : ''
                }`}
              >
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border font-mono text-xs font-semibold ${
                    RANK_STYLES[entry.rank] || 'border-ink-600 bg-ink-900 text-mist-500'
                  }`}
                >
                  {entry.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-mist-100">
                    {entry.name}
                    {entry.is_you && <span className="ml-2 text-xs text-pulse-400">(you)</span>}
                  </p>
                  <p className="text-xs text-mist-500">Top {entry.percentile}%</p>
                </div>
                <span className="font-mono text-lg text-mist-100">{Math.round(entry.overall_score)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
