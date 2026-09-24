import { useState } from 'react'
import Sidebar from '../components/Sidebar'
import OverviewTab from './OverviewTab'
import RepositoriesTab from './RepositoriesTab'
import AchievementsTab from './AchievementsTab'
import LeaderboardTab from './LeaderboardTab'
import AICoachTab from './AICoachTab'

const TAB_COMPONENTS = {
  overview: OverviewTab,
  repositories: RepositoriesTab,
  achievements: AchievementsTab,
  leaderboard: LeaderboardTab,
  ai: AICoachTab,
}

export default function Dashboard() {
  const [active, setActive] = useState('overview')
  const ActiveTab = TAB_COMPONENTS[active] || OverviewTab

  return (
    <div className="flex min-h-screen bg-ink-950">
      <Sidebar active={active} onChange={setActive} />
      <main className="flex-1 overflow-y-auto px-6 py-8 sm:px-10 lg:px-14">
        <div className="mx-auto max-w-5xl">
          <ActiveTab />
        </div>
      </main>
    </div>
  )
}
