import { useState } from 'react'
import { ApiError } from '../../api/errors'
import { ErrorNotice } from '../../components/ErrorNotice'
import { useAuth } from '../auth/AuthContext'
import {
  buildPatient as buildDiabetesPatient,
  toFormValues as toDiabetesFormValues,
  type FormValues as DiabetesFormValues,
} from '../diabetes/form'
import {
  useFeatures as useDiabetesFeatures,
  usePrediction as useDiabetesPrediction,
} from '../diabetes/hooks'
import { PatientForm as DiabetesPatientForm } from '../diabetes/PatientForm'
import {
  buildPatient as buildHeartPatient,
  toFormValues as toHeartFormValues,
  type FormValues as HeartFormValues,
} from '../heart/form'
import {
  useFeatures as useHeartFeatures,
  usePrediction as useHeartPrediction,
} from '../heart/hooks'
import { PatientForm as HeartPatientForm } from '../heart/PatientForm'
import { PatientHistoryView } from './PatientHistoryView'
import { SimplePredictionResult } from './SimplePredictionResult'

export type PatientTab = 'overview' | 'assessment' | 'history' | 'profile'
export type AssessmentCondition = 'heart' | 'diabetes'

export function PatientDashboard() {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState<PatientTab>('overview')
  const [condition, setCondition] = useState<AssessmentCondition>('heart')

  // Heart state
  const heartFeatures = useHeartFeatures()
  const heartPrediction = useHeartPrediction()
  const [heartValues, setHeartValues] = useState<HeartFormValues>({})

  // Diabetes state
  const diabetesFeatures = useDiabetesFeatures()
  const diabetesPrediction = useDiabetesPrediction()
  const [diabetesValues, setDiabetesValues] = useState<DiabetesFormValues>({})

  function startAssessment(cond: AssessmentCondition) {
    setCondition(cond)
    setTab('assessment')
  }

  return (
    <div className="patient-dashboard" style={{ marginTop: '0.5rem' }}>
      {/* Patient Sub-Navigation */}
      <nav className="patient-nav" aria-label="Patient navigation">
        <button
          type="button"
          className={tab === 'overview' ? 'patient-tab-btn active' : 'patient-tab-btn'}
          onClick={() => setTab('overview')}
        >
          Overview
        </button>
        <button
          type="button"
          className={tab === 'assessment' ? 'patient-tab-btn active' : 'patient-tab-btn'}
          onClick={() => setTab('assessment')}
        >
          New Assessment
        </button>
        <button
          type="button"
          className={tab === 'history' ? 'patient-tab-btn active' : 'patient-tab-btn'}
          onClick={() => setTab('history')}
        >
          My History &amp; Reports
        </button>
        <button
          type="button"
          className={tab === 'profile' ? 'patient-tab-btn active' : 'patient-tab-btn'}
          onClick={() => setTab('profile')}
        >
          My Account
        </button>
      </nav>

      {/* TAB 1: OVERVIEW */}
      {tab === 'overview' && (
        <div className="patient-tab-content">
          <div
            className="panel"
            style={{
              padding: '2rem',
              marginBottom: '1.5rem',
              background: 'linear-gradient(135deg, #0f2942 0%, #1e3a5f 100%)',
              color: '#ffffff',
              borderRadius: 'var(--radius)',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                background: 'rgba(255, 255, 255, 0.15)',
                fontSize: '0.8rem',
                fontWeight: 600,
                marginBottom: '0.75rem',
              }}
            >
              Patient Portal
            </span>
            <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', color: '#ffffff' }}>
              Welcome, {user?.full_name || 'Patient'}
            </h1>
            <p
              style={{ maxWidth: '600px', fontSize: '0.95rem', color: '#cbd5e1', lineHeight: 1.6 }}
            >
              ClariDx provides transparent clinical decision support. Explore your health
              indicators, run multi-model assessments, and download verified PDF reports.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            <div
              className="panel"
              style={{
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '0.5rem',
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#e11d48"
                    strokeWidth="2"
                  >
                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                  </svg>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>
                    Heart Disease Assessment
                  </strong>
                </div>
                <p className="hint" style={{ marginBottom: '1.25rem' }}>
                  Evaluate cardiovascular risk indicators using 4 machine learning models with
                  explainable factor breakdown.
                </p>
              </div>
              <button type="button" className="primary" onClick={() => startAssessment('heart')}>
                Start Heart Assessment
              </button>
            </div>

            <div
              className="panel"
              style={{
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '0.5rem',
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="2"
                  >
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                  </svg>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>
                    Type 2 Diabetes Assessment
                  </strong>
                </div>
                <p className="hint" style={{ marginBottom: '1.25rem' }}>
                  Assess metabolic and diagnostic indicators including glucose, BMI, and blood
                  pressure with transparent explanations.
                </p>
              </div>
              <button type="button" className="primary" onClick={() => startAssessment('diabetes')}>
                Start Diabetes Assessment
              </button>
            </div>

            <div
              className="panel"
              style={{
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '0.5rem',
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#059669"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>
                    My Past Reports
                  </strong>
                </div>
                <p className="hint" style={{ marginBottom: '1.25rem' }}>
                  Review your saved clinical decision-support history, factor contributions, and
                  download official PDF summaries.
                </p>
              </div>
              <button type="button" className="secondary" onClick={() => setTab('history')}>
                View Past Records
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: NEW ASSESSMENT */}
      {tab === 'assessment' && (
        <div>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <button
              type="button"
              className={condition === 'heart' ? 'condition-btn active' : 'condition-btn'}
              onClick={() => setCondition('heart')}
            >
              Heart Disease
            </button>
            <button
              type="button"
              className={condition === 'diabetes' ? 'condition-btn active' : 'condition-btn'}
              onClick={() => setCondition('diabetes')}
            >
              Diabetes
            </button>
          </div>

          {condition === 'heart' ? (
            <div>
              {heartFeatures.isPending ? (
                <p role="status">Loading heart measurements form…</p>
              ) : heartFeatures.isError ? (
                <ErrorNotice
                  title="Cannot load form"
                  error={heartFeatures.error}
                  onRetry={() => void heartFeatures.refetch()}
                />
              ) : (
                <>
                  {!heartPrediction.isSuccess && (
                    <HeartPatientForm
                      specs={heartFeatures.data}
                      values={heartValues}
                      onChange={(name, value) => {
                        heartPrediction.reset()
                        setHeartValues((prev) => ({ ...prev, [name]: value }))
                      }}
                      onApplyExample={(patient) => {
                        heartPrediction.reset()
                        setHeartValues(toHeartFormValues(patient))
                      }}
                      onClear={() => {
                        heartPrediction.reset()
                        setHeartValues({})
                      }}
                      modelName="random_forest"
                      onModelChange={() => {}}
                      serverIssues={
                        heartPrediction.error instanceof ApiError
                          ? heartPrediction.error.issues
                          : []
                      }
                      submitting={heartPrediction.isPending}
                      onSubmit={() =>
                        heartPrediction.mutate({
                          patient: buildHeartPatient(heartFeatures.data, heartValues),
                          modelName: 'random_forest',
                        })
                      }
                      canPredict={true}
                      hideModelSelector={true}
                    />
                  )}

                  {heartPrediction.isPending && (
                    <div
                      className="panel"
                      style={{ padding: '2rem', textAlign: 'center', marginTop: '1rem' }}
                    >
                      <p role="status">
                        Running all 4 machine learning models and evaluating consensus…
                      </p>
                    </div>
                  )}

                  {heartPrediction.isError && (
                    <div style={{ marginTop: '1rem' }}>
                      <ErrorNotice
                        title="Assessment could not be completed"
                        error={heartPrediction.error}
                      />
                    </div>
                  )}

                  {heartPrediction.isSuccess && (
                    <SimplePredictionResult
                      condition="heart"
                      result={heartPrediction.data}
                      onReset={() => {
                        heartPrediction.reset()
                        setHeartValues({})
                      }}
                    />
                  )}
                </>
              )}
            </div>
          ) : (
            <div>
              {diabetesFeatures.isPending ? (
                <p role="status">Loading diabetes measurements form…</p>
              ) : diabetesFeatures.isError ? (
                <ErrorNotice
                  title="Cannot load form"
                  error={diabetesFeatures.error}
                  onRetry={() => void diabetesFeatures.refetch()}
                />
              ) : (
                <>
                  {!diabetesPrediction.isSuccess && (
                    <DiabetesPatientForm
                      specs={diabetesFeatures.data}
                      values={diabetesValues}
                      onChange={(name, value) => {
                        diabetesPrediction.reset()
                        setDiabetesValues((prev) => ({ ...prev, [name]: value }))
                      }}
                      onApplyExample={(patient) => {
                        diabetesPrediction.reset()
                        setDiabetesValues(toDiabetesFormValues(patient))
                      }}
                      onClear={() => {
                        diabetesPrediction.reset()
                        setDiabetesValues({})
                      }}
                      modelName="logistic_regression"
                      onModelChange={() => {}}
                      serverIssues={
                        diabetesPrediction.error instanceof ApiError
                          ? diabetesPrediction.error.issues
                          : []
                      }
                      submitting={diabetesPrediction.isPending}
                      onSubmit={() =>
                        diabetesPrediction.mutate({
                          patient: buildDiabetesPatient(diabetesFeatures.data, diabetesValues),
                          modelName: 'logistic_regression',
                        })
                      }
                      canPredict={true}
                      hideModelSelector={true}
                    />
                  )}

                  {diabetesPrediction.isPending && (
                    <div
                      className="panel"
                      style={{ padding: '2rem', textAlign: 'center', marginTop: '1rem' }}
                    >
                      <p role="status">
                        Running all 4 machine learning models and evaluating consensus…
                      </p>
                    </div>
                  )}

                  {diabetesPrediction.isError && (
                    <div style={{ marginTop: '1rem' }}>
                      <ErrorNotice
                        title="Assessment could not be completed"
                        error={diabetesPrediction.error}
                      />
                    </div>
                  )}

                  {diabetesPrediction.isSuccess && (
                    <SimplePredictionResult
                      condition="diabetes"
                      result={diabetesPrediction.data}
                      onReset={() => {
                        diabetesPrediction.reset()
                        setDiabetesValues({})
                      }}
                    />
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: HISTORY */}
      {tab === 'history' && (
        <div className="patient-tab-content">
          <PatientHistoryView onStartAssessment={() => setTab('assessment')} />
        </div>
      )}

      {/* TAB 4: MY ACCOUNT */}
      {tab === 'profile' && (
        <div className="patient-tab-content">
          <div className="panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div
              className="panel-header"
              style={{
                marginBottom: '1.5rem',
                borderBottom: '1px solid var(--border)',
                paddingBottom: '1rem',
              }}
            >
              <h2>My Patient Account</h2>
              <p className="hint">Account credentials and session security settings.</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  background: 'var(--surface-raised)',
                  borderRadius: 'var(--radius)',
                }}
              >
                <span style={{ color: 'var(--text-secondary)' }}>Full Name:</span>
                <strong>{user?.full_name || 'N/A'}</strong>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  background: 'var(--surface-raised)',
                  borderRadius: 'var(--radius)',
                }}
              >
                <span style={{ color: 'var(--text-secondary)' }}>Email Address:</span>
                <strong>{user?.email}</strong>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  background: 'var(--surface-raised)',
                  borderRadius: 'var(--radius)',
                }}
              >
                <span style={{ color: 'var(--text-secondary)' }}>Account Role:</span>
                <span className="role-badge role-patient">PATIENT</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  background: 'var(--surface-raised)',
                  borderRadius: 'var(--radius)',
                }}
              >
                <span style={{ color: 'var(--text-secondary)' }}>Security:</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--success)' }}>
                  Argon2id Hashed &bull; JWT Authenticated
                </span>
              </div>
            </div>

            <div
              style={{
                marginTop: '2rem',
                borderTop: '1px solid var(--border)',
                paddingTop: '1.25rem',
                textAlign: 'right',
              }}
            >
              <button type="button" className="secondary" onClick={logout}>
                Sign Out of ClariDx
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
