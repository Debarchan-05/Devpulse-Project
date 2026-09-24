import { useState } from 'react'
import { ActivitySquare } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui'
import PulseMark from '../components/PulseMark'

export default function AuthScreen() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login') // login | register
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.name, form.email, form.password)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink-950 px-4">
      <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 opacity-[0.06]">
        <PulseMark width="100%" height={280} animated={false} />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <ActivitySquare size={30} className="text-pulse-500" strokeWidth={1.75} />
          <div>
            <h1 className="font-display text-2xl font-bold text-mist-100">DevPulse</h1>
            <p className="mt-1 text-sm text-mist-500">Your GitHub profile, tracked like a vitals monitor.</p>
          </div>
        </div>

        <div className="rounded-2xl border border-ink-700 bg-ink-800/70 p-6 shadow-2xl shadow-black/40">
          <div className="mb-6 flex rounded-xl bg-ink-900 p-1 text-sm">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m)
                  setError('')
                }}
                className={`flex-1 rounded-lg py-2 font-medium capitalize transition ${
                  mode === m ? 'bg-pulse-500 text-ink-950' : 'text-mist-500 hover:text-mist-100'
                }`}
              >
                {m === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="flex flex-col gap-4">
            {mode === 'register' && (
              <Field label="Name">
                <input
                  required
                  minLength={2}
                  value={form.name}
                  onChange={update('name')}
                  className="input"
                  placeholder="Ada Lovelace"
                />
              </Field>
            )}
            <Field label="Email">
              <input
                required
                type="email"
                value={form.email}
                onChange={update('email')}
                className="input"
                placeholder="you@example.com"
              />
            </Field>
            <Field label="Password">
              <input
                required
                minLength={8}
                type="password"
                value={form.password}
                onChange={update('password')}
                className="input"
                placeholder="At least 8 characters"
              />
            </Field>

            {error && (
              <p className="rounded-lg border border-pulse-500/30 bg-pulse-500/10 px-3 py-2 text-xs text-pulse-400">
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} className="mt-1 w-full">
              {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center font-mono text-[11px] text-mist-500">
          FastAPI · SQLAlchemy · MySQL — running on your machine
        </p>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="text-xs font-medium uppercase tracking-wide text-mist-500">{label}</span>
      {children}
    </label>
  )
}
