import { useEffect, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, ErrorNote } from '../components/ui'
import { PageHeader } from './OverviewTab'

const TONES = ['professional', 'concise', 'impact']

export default function AICoachTab() {
  const [mode, setMode] = useState('career')
  const [targetRole, setTargetRole] = useState('Backend Developer')
  const [tone, setTone] = useState('professional')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [reports, setReports] = useState([])

  const loadReports = () => api.getReports().then(setReports).catch(() => {})

  useEffect(() => {
    loadReports()
  }, [])

  const generate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const report =
        mode === 'career' ? await api.careerAnalysis(targetRole) : await api.resumeBullets(targetRole, tone)
      setResult(report)
      loadReports()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="AI Coach" subtitle="Career feedback and resume bullets, generated from your real Pulse data." />

      <div className="flex gap-1 rounded-xl bg-ink-800 p-1 w-fit">
        {[
          { id: 'career', label: 'Career analysis' },
          { id: 'resume', label: 'Resume bullets' },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setMode(m.id)
              setResult(null)
              setError('')
            }}
            className={`rounded-lg px-4 py-2 text-xs font-medium transition ${
              mode === m.id ? 'bg-pulse-500 text-ink-950' : 'text-mist-500 hover:text-mist-100'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <Card className="p-6">
        <form onSubmit={generate} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-xs font-medium uppercase tracking-wide text-mist-500">Target role</span>
            <input
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              required
              minLength={2}
              className="input max-w-sm"
              placeholder="e.g. Backend Developer"
            />
          </label>

          {mode === 'resume' && (
            <div className="flex gap-2">
              {TONES.map((t) => (
                <button
                  type="button"
                  key={t}
                  onClick={() => setTone(t)}
                  className={`rounded-full border px-3 py-1.5 text-xs capitalize transition ${
                    tone === t
                      ? 'border-pulse-500 bg-pulse-500/15 text-pulse-400'
                      : 'border-ink-600 text-mist-500 hover:text-mist-100'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          )}

          <Button type="submit" disabled={loading} className="w-fit">
            <Sparkles size={15} />
            {loading ? 'Thinking…' : mode === 'career' ? 'Generate career analysis' : 'Generate resume bullets'}
          </Button>
        </form>

        {error && (
          <div className="mt-4">
            <ErrorNote message={error} />
          </div>
        )}

        {result && (
          <div className="mt-6 whitespace-pre-wrap rounded-xl border border-ink-700 bg-ink-900 p-5 text-sm leading-relaxed text-mist-300">
            {result.content}
          </div>
        )}
      </Card>

      {reports.length > 0 && (
        <div>
          <h3 className="mb-3 font-display text-sm font-semibold text-mist-100">Report history</h3>
          <div className="flex flex-col gap-2">
            {reports.map((r) => (
              <details key={r.id} className="rounded-xl border border-ink-700 bg-ink-800/50 px-4 py-3">
                <summary className="flex cursor-pointer items-center justify-between text-xs">
                  <span className="font-mono uppercase tracking-wide text-mist-500">
                    {r.report_type.replace('_', ' ')}
                  </span>
                </summary>
                <p className="mt-3 whitespace-pre-wrap text-sm text-mist-300">{r.content}</p>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
