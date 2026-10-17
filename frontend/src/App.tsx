import { useState } from 'react'
import { AuthProvider, useAuth } from './features/auth/AuthContext'
import { LoginForm } from './features/auth/LoginForm'
import { ResearcherNotice } from './features/auth/ResearcherNotice'
import { PredictionPage as DiabetesPredictionPage } from './features/diabetes/PredictionPage'
import { PredictionPage as HeartPredictionPage } from './features/heart/PredictionPage'

export type Condition = 'heart' | 'diabetes'

export function AppContent() {
  const { user, isAuthenticated, isLoading, logout } = useAuth()
  const [condition, setCondition] = useState<Condition>('heart')

  return (
    <>
      <header className="app-header">
        <div className="container header-container">
          <div className="brand">
            <h1>ClariDx</h1>
            <p>Clinical AI you can see through</p>
          </div>
          {isAuthenticated && user && (
            <div className="user-nav">
              <div className="user-profile">
                <span className="user-name">{user.full_name || user.email}</span>
                <span className={`role-badge role-${user.role.toLowerCase()}`}>
                  {user.role.toUpperCase()}
                </span>
              </div>
              <button
                type="button"
                className="secondary sign-out-btn"
                onClick={logout}
                aria-label="Sign out"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="container">
        <p className="banner" role="note">
          Research prototype for decision support and education only. It is not a medical device and
          must not be used for diagnosis or treatment.
        </p>

        {isLoading ? (
          <p role="status" className="session-loading">
            Loading session\u2026
          </p>
        ) : !isAuthenticated ? (
          <LoginForm />
        ) : (
          <>
            {user?.role?.toLowerCase() === 'researcher' && <ResearcherNotice />}
            <nav className="condition-nav" aria-label="Condition selector">
              <div className="condition-selector" role="group" aria-label="Conditions">
                <button
                  type="button"
                  className={
                    condition === 'heart' ? 'condition-btn active' : 'condition-btn secondary'
                  }
                  aria-pressed={condition === 'heart'}
                  onClick={() => setCondition('heart')}
                >
                  Heart Disease
                </button>
                <button
                  type="button"
                  className={
                    condition === 'diabetes' ? 'condition-btn active' : 'condition-btn secondary'
                  }
                  aria-pressed={condition === 'diabetes'}
                  onClick={() => setCondition('diabetes')}
                >
                  Diabetes
                </button>
              </div>
            </nav>

            {condition === 'heart' ? (
              <HeartPredictionPage key="heart" />
            ) : (
              <DiabetesPredictionPage key="diabetes" />
            )}
          </>
        )}
      </main>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
