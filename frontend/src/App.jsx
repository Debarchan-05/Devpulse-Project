import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import AuthScreen from './pages/AuthScreen'
import Dashboard from './pages/Dashboard'
import { Loader } from './components/ui'

function Root() {
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink-950">
        <Loader label="Booting DevPulse…" />
      </div>
    )
  }

  return status === 'authed' ? <Dashboard /> : <AuthScreen />
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Root />
      </AuthProvider>
    </ToastProvider>
  )
}
