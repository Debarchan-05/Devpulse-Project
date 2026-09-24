import { useEffect, useState } from 'react'
import { Award } from 'lucide-react'
import { api } from '../api/client'
import { Card, EmptyState, ErrorNote, Loader } from '../components/ui'
import { PageHeader } from './OverviewTab'
import { formatDate } from '../lib/pulse'

export default function AchievementsTab() {
  const [badges, setBadges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .getAchievements()
      .then(setBadges)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const earnedCount = badges.filter((b) => b.earned).length

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Achievements"
        subtitle={loading ? 'Loading Pulse Badges…' : `${earnedCount} of ${badges.length} Pulse Badges earned`}
      />

      {error && <ErrorNote message={error} />}
      {loading ? (
        <Loader label="Checking the badge case…" />
      ) : badges.length === 0 ? (
        <EmptyState icon={Award} title="No badges yet" description="Sync a GitHub profile to start earning Pulse Badges." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {badges.map((badge) => (
            <Card
              key={badge.code}
              className={`flex flex-col gap-2 p-5 transition ${badge.earned ? 'border-signal-500/30' : 'opacity-50 grayscale'}`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl leading-none">{badge.icon}</span>
                <h3 className="font-display text-sm font-semibold text-mist-100">{badge.name}</h3>
              </div>
              <p className="text-xs text-mist-500">{badge.description}</p>
              {badge.earned ? (
                <p className="mt-1 font-mono text-[10px] text-signal-400">Earned {formatDate(badge.earned_at)}</p>
              ) : (
                <p className="mt-1 font-mono text-[10px] text-mist-500">Not yet unlocked</p>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
