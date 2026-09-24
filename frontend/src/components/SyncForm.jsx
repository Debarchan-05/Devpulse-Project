import { useState } from 'react'
import { GitBranch, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import { Button } from './ui'

export default function SyncForm({ compact = false, onSynced }) {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    if (!username.trim()) return
    setLoading(true)
    setError('')
    try {
      const result = await api.syncGithub(username.trim())
      onSynced?.(result)
      if (!compact) setUsername('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (compact) {
    return (
      <form onSubmit={submit} className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="GitHub username"
            className="input !py-2 w-44"
          />
          <Button type="submit" variant="subtle" disabled={loading} className="!px-3 !py-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? '' : 'Sync'}
          </Button>
        </div>
        {error && <p className="max-w-[15rem] text-right text-xs text-pulse-400">{error}</p>}
      </form>
    )
  }

  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-2xl border border-dashed border-ink-600 px-8 py-14 text-center">
      <GitBranch size={30} className="text-mist-500" strokeWidth={1.5} />
      <div>
        <h3 className="font-display text-lg font-semibold text-mist-100">Connect a GitHub profile</h3>
        <p className="mt-1 text-sm text-mist-500">
          Sync any public GitHub username to compute a Pulse Score, unlock badges, and start tracking growth.
        </p>
      </div>
      <form onSubmit={submit} className="flex w-full max-w-xs flex-col gap-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g. torvalds"
          className="input text-center"
          autoFocus
        />
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? 'Syncing…' : 'Sync GitHub Profile'}
        </Button>
      </form>
      {error && <p className="text-xs text-pulse-400">{error}</p>}
    </div>
  )
}
