import { useState } from 'react'
import { AuthProvider, useAuth } from './features/auth/AuthContext'
import { LoginForm } from './features/auth/LoginForm'
import { RegisterForm } from './features/auth/RegisterForm'
import { RequestAccessPage } from './features/auth/RequestAccessPage'
import { ResearcherNotice } from './features/auth/ResearcherNotice'
import { PredictionPage as DiabetesPredictionPage } from './features/diabetes/PredictionPage'
import { PredictionPage as HeartPredictionPage } from './features/heart/PredictionPage'
import { PatientDashboard } from './features/patient/PatientDashboard'

export type Condition = 'heart' | 'diabetes'
export type View = 'login' | 'register' | 'request-access'

export function AppContent() {
  const { user, isAuthenticated, isLoading, logout } = useAuth()
  const [condition, setCondition] = useState<Condition>('heart')
  const [view, setView] = useState<View>('login')

  const handleLogout = () => {
    setView('login')
    logout()
  }

  const isPatient = user?.role?.toLowerCase() === 'patient'
  const isResearcher = user?.role?.toLowerCase() === 'researcher'

  return (
    <div className="app-root">
      {/* ===== Header ===== */}
      <header className="app-header">
        <div className="container header-inner">
          <div className="brand">
            <div className="brand-mark" aria-hidden="true">
              Cx
            </div>
            <div className="brand-text">
              <h1 className="brand-name">ClariDx</h1>
              <p className="brand-tagline">Clinical AI you can see through</p>
            </div>
          </div>

          {isAuthenticated && user && (
            <nav className="user-nav" aria-label="User account">
              <div className="user-profile">
                <span className="user-name">{user.full_name || user.email}</span>
                <span
                  className={`role-badge role-${user.role.toLowerCase()}`}
                  aria-label={`Role: ${user.role}`}
                >
                  {user.role.toUpperCase()}
                </span>
              </div>
              <button
                type="button"
                className="sign-out-btn"
                onClick={handleLogout}
                aria-label="Sign out of ClariDx"
              >
                Sign out
              </button>
            </nav>
          )}
        </div>
      </header>

      {/* ===== Disclaimer ===== */}
      <div className="disclaimer-banner" role="note">
        Research prototype for decision support and education only. It is not a medical device and
        must not be used for diagnosis or treatment.
      </div>

      {/* ===== Main Content ===== */}
      <main className="app-main">
        <div className="container">
          {isLoading ? (
            <p role="status" className="session-loading">
              Loading session…
            </p>
          ) : !isAuthenticated ? (
            view === 'register' ? (
              <RegisterForm onBackToLogin={() => setView('login')} />
            ) : view === 'request-access' ? (
              <RequestAccessPage onBack={() => setView('login')} />
            ) : (
              <LoginForm
                onRequestAccess={() => setView('request-access')}
                onRegister={() => setView('register')}
              />
            )
          ) : isPatient ? (
            <PatientDashboard />
          ) : (
            <>
              {isResearcher && <ResearcherNotice />}

              <div className="workspace-header">
                <h1 className="workspace-title">
                  {isResearcher ? 'Model Inspection Workspace' : 'Clinical Decision Support'}
                </h1>
                <p className="workspace-subtitle">
                  {isResearcher
                    ? 'Inspect feature definitions and model parameters across conditions.'
                    : 'Analyse patient measurements and review explainable AI predictions.'}
                </p>
              </div>

              <nav className="condition-nav" aria-label="Condition selector">
                <button
                  type="button"
                  className={condition === 'heart' ? 'condition-btn active' : 'condition-btn'}
                  aria-pressed={condition === 'heart'}
                  onClick={() => setCondition('heart')}
                >
                  <span className="btn-icon" aria-hidden="true">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                    </svg>
                  </span>
                  Heart Disease
                </button>
                <button
                  type="button"
                  className={condition === 'diabetes' ? 'condition-btn active' : 'condition-btn'}
                  aria-pressed={condition === 'diabetes'}
                  onClick={() => setCondition('diabetes')}
                >
                  <span className="btn-icon" aria-hidden="true">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                    </svg>
                  </span>
                  Diabetes
                </button>
              </nav>

              {condition === 'heart' ? (
                <HeartPredictionPage key="heart" />
              ) : (
                <DiabetesPredictionPage key="diabetes" />
              )}
            </>
          )}
        </div>
      </main>

      {/* ===== Footer ===== */}
      <footer className="app-footer">
        <div className="container footer-inner">
          <span className="footer-brand">ClariDx</span>
          <span className="footer-meta">
            Explainable AI for Clinical Decision Support · Research prototype only
          </span>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
