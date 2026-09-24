export default function PulseMark({ width = 148, height = 36, className = '', animated = true }) {
  return (
    <svg viewBox="0 0 160 40" width={width} height={height} className={className} fill="none" aria-hidden="true">
      <path
        d="M0 20 H38 L46 6 L57 34 L65 20 H80 L86 12 L94 28 L100 20 H160"
        stroke="var(--color-pulse-500)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={animated ? 'pulse-line' : ''}
      />
    </svg>
  )
}
