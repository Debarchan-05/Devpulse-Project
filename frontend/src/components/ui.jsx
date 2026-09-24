import PulseMark from './PulseMark'

export function Card({ children, className = '' }) {
  return (
    <div className={`rounded-2xl border border-ink-700 bg-ink-800/70 ${className}`}>
      {children}
    </div>
  )
}

export function Button({ children, variant = 'primary', className = '', ...props }) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50'
  const variants = {
    primary: 'bg-pulse-500 text-ink-950 hover:bg-pulse-400 shadow-[0_0_0_1px_rgba(255,92,77,0.3)]',
    ghost: 'border border-ink-600 text-mist-100 hover:border-pulse-500/50 hover:text-pulse-400',
    subtle: 'bg-ink-700 text-mist-100 hover:bg-ink-600',
  }
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Loader({ label = 'Reading vitals…' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-mist-500">
      <PulseMark width={120} height={30} />
      <p className="font-mono text-xs tracking-wide">{label}</p>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-ink-600 px-6 py-16 text-center">
      {Icon && <Icon size={28} className="text-mist-500" strokeWidth={1.5} />}
      <h3 className="font-display text-base font-semibold text-mist-100">{title}</h3>
      {description && <p className="max-w-sm text-sm text-mist-500">{description}</p>}
      {action}
    </div>
  )
}

export function PillarBar({ label, value, colorClass = 'bg-pulse-500' }) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-mist-500">{label}</span>
        <span className="font-mono text-sm text-mist-100">{Math.round(value)}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
        <div
          className={`h-full rounded-full ${colorClass} transition-all duration-700`}
          style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
        />
      </div>
    </div>
  )
}

export function ErrorNote({ message }) {
  if (!message) return null
  return (
    <div className="rounded-xl border border-pulse-500/30 bg-pulse-500/10 px-4 py-3 text-sm text-pulse-400">
      {message}
    </div>
  )
}
