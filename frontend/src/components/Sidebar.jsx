import { Activity, Award, FolderGit2, LogOut, Sparkles, Trophy } from 'lucide-react'
import PulseMark from './PulseMark'
import { useAuth } from '../context/AuthContext'

const TABS = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'repositories', label: 'Repositories', icon: FolderGit2 },
  { id: 'achievements', label: 'Achievements', icon: Award },
  { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
  { id: 'ai', label: 'AI Coach', icon: Sparkles },
]

export default function Sidebar({ active, onChange }) {
  const { user, logout } = useAuth()

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-ink-700 bg-ink-900/60 px-4 py-6">
      <div className="mb-8 flex items-center gap-2 px-2">
        <PulseMark width={128} height={30} />
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = active === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-pulse-500/15 text-pulse-400 ring-1 ring-pulse-500/30'
                  : 'text-mist-500 hover:bg-ink-800 hover:text-mist-100'
              }`}
            >
              <Icon size={17} strokeWidth={1.75} />
              {tab.label}
            </button>
          )
        })}
      </nav>

      <div className="mt-auto flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-800/60 px-3 py-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ink-700 font-display text-sm font-semibold text-mist-100">
          {user?.name?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-mist-100">{user?.name}</p>
          <p className="truncate text-xs text-mist-500">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          title="Log out"
          className="rounded-lg p-1.5 text-mist-500 transition hover:bg-ink-700 hover:text-pulse-400"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  )
}
