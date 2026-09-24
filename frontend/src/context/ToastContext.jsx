import { createContext, useCallback, useContext, useState } from 'react'

const ToastContext = createContext(null)
let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const remove = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (message, type = 'info', duration = 4500) => {
      const id = ++idCounter
      setToasts((list) => [...list, { id, message, type }])
      if (duration) setTimeout(() => remove(id), duration)
    },
    [remove],
  )

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex w-[22rem] max-w-[90vw] flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              'animate-[fadeIn_.2s_ease-out] rounded-xl border px-4 py-3 text-sm shadow-xl backdrop-blur-md ' +
              (t.type === 'success'
                ? 'border-signal-500/40 bg-ink-800/95 text-signal-400'
                : t.type === 'error'
                  ? 'border-pulse-500/40 bg-ink-800/95 text-pulse-400'
                  : 'border-ink-600 bg-ink-800/95 text-mist-300')
            }
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
