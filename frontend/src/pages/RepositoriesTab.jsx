import { useEffect, useState } from 'react'
import { Archive, ExternalLink, FolderGit2, ShieldCheck, Star } from 'lucide-react'
import { api } from '../api/client'
import { Card, EmptyState, ErrorNote, Loader, PillarBar } from '../components/ui'
import { PageHeader } from './OverviewTab'

const SORTS = [
  { id: 'stars', label: 'Stars' },
  { id: 'health', label: 'Health' },
  { id: 'name', label: 'Name' },
]

export default function RepositoriesTab() {
  const [repos, setRepos] = useState([])
  const [sortBy, setSortBy] = useState('stars')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    api
      .getRepositories(sortBy)
      .then(setRepos)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [sortBy])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader title="Repositories" subtitle="Every synced repo, with its own Health Score." />
        <div className="flex gap-1 rounded-xl bg-ink-800 p-1">
          {SORTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSortBy(s.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                sortBy === s.id ? 'bg-pulse-500 text-ink-950' : 'text-mist-500 hover:text-mist-100'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorNote message={error} />}
      {loading ? (
        <Loader label="Fetching repositories…" />
      ) : repos.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories yet"
          description="Sync a GitHub profile from the Overview tab to see repositories here."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {repos.map((repo) => (
            <Card key={repo.id} className="flex flex-col gap-3 p-5">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 truncate font-display text-sm font-semibold text-mist-100 hover:text-pulse-400"
                  >
                    {repo.name}
                    <ExternalLink size={12} className="shrink-0 text-mist-500" />
                  </a>
                  {repo.description && <p className="mt-1 line-clamp-2 text-xs text-mist-500">{repo.description}</p>}
                </div>
                {repo.is_archived && (
                  <span className="flex shrink-0 items-center gap-1 rounded-full bg-ink-700 px-2 py-0.5 text-[10px] text-mist-500">
                    <Archive size={10} /> archived
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 font-mono text-xs text-mist-500">
                {repo.language && <span className="rounded-full border border-ink-600 px-2 py-0.5">{repo.language}</span>}
                <span className="flex items-center gap-1">
                  <Star size={12} /> {repo.stars}
                </span>
                {repo.has_license && (
                  <span className="flex items-center gap-1 text-signal-400">
                    <ShieldCheck size={12} /> licensed
                  </span>
                )}
              </div>

              {repo.topics?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {repo.topics.slice(0, 4).map((topic) => (
                    <span key={topic} className="rounded-full bg-ink-900 px-2 py-0.5 text-[10px] text-mist-500">
                      {topic}
                    </span>
                  ))}
                </div>
              )}

              <PillarBar label="Repo health" value={repo.repo_health_score} colorClass="bg-signal-500" />
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
