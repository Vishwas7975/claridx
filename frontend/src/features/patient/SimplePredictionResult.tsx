import { useState } from 'react'
import type { DiabetesPredictionResponse, PredictionResponse } from '../../api/types'
import { useAuth } from '../auth/AuthContext'

interface Props {
  condition: 'heart' | 'diabetes'
  result: PredictionResponse | DiabetesPredictionResponse
  onReset: () => void
}

export function SimplePredictionResult({ condition, result, onReset }: Props) {
  const { token } = useAuth()
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const isPositive = result.ensemble?.predicted_positive ?? result.predicted_positive
  const conditionTitle =
    condition === 'heart' ? 'Heart Disease Risk Assessment' : 'Type 2 Diabetes Risk Assessment'

  // Top 4 factors from SHAP
  const topFactors = result.shap.contributions.slice(0, 4)

  async function handleDownloadPdf() {
    if (!result.record_id) return
    setDownloading(true)
    setDownloadError(null)
    try {
      const res = await fetch(`/api/v1/history/${result.record_id}/pdf`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (!res.ok) {
        throw new Error(`Failed to download report (${res.status})`)
      }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `claridx_${condition}_${result.record_id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setDownloadError('Could not generate PDF report. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="panel patient-result-panel" style={{ marginTop: '1.5rem' }}>
      <div
        className="panel-header"
        style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}
      >
        <span
          className="badge-patient-condition"
          style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}
        >
          {conditionTitle}
        </span>
        <h2 style={{ fontSize: '1.5rem', marginTop: '0.25rem', color: 'var(--primary)' }}>
          Assessment Results
        </h2>
        <p className="hint">Simple, transparent summary of your AI decision-support evaluation.</p>
      </div>

      {/* Outcome Banner */}
      <div
        className={`patient-outcome-card ${isPositive ? 'outcome-elevated' : 'outcome-lower'}`}
        style={{
          padding: '1.25rem',
          borderRadius: 'var(--radius)',
          margin: '1.25rem 0',
          backgroundColor: isPositive ? '#fef3c7' : '#ecfdf5',
          border: `1px solid ${isPositive ? '#fde68a' : '#a7f3d0'}`,
        }}
      >
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}
        >
          <span
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.85rem',
              fontWeight: 700,
              backgroundColor: isPositive ? '#d97706' : '#059669',
              color: '#ffffff',
            }}
          >
            {isPositive ? 'Elevated Risk' : 'Lower Risk'}
          </span>
          <strong style={{ fontSize: '1.15rem', color: isPositive ? '#92400e' : '#065f46' }}>
            {isPositive ? 'Elevated Risk Detected' : 'Lower Risk Indicated'}
          </strong>
        </div>
        <p
          style={{
            fontSize: '0.95rem',
            color: isPositive ? '#78350f' : '#047857',
            margin: 0,
            lineHeight: 1.5,
          }}
        >
          {isPositive
            ? 'Based on the entered physiological measurements, the AI decision-support models indicate patterns associated with elevated risk. This is not a diagnosis, but suggests clinical follow-up may be beneficial.'
            : 'Based on the entered measurements, the decision-support models do not identify elevated risk patterns. Continue routine preventive health practices and regular checkups.'}
        </p>
      </div>

      {/* Consensus Breakdown */}
      {result.ensemble && (
        <div
          style={{
            background: 'var(--surface-raised)',
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius)',
            marginBottom: '1.5rem',
            border: '1px solid var(--border)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <div>
              <strong style={{ fontSize: '0.95rem', color: 'var(--primary)' }}>
                Multi-Model Consensus: {result.ensemble.votes_positive} of{' '}
                {result.ensemble.total_models_evaluated} models indicated elevated risk
              </strong>
              <p className="hint" style={{ marginTop: '0.2rem' }}>
                Evaluated automatically across Random Forest, Logistic Regression, Gradient
                Boosting, and MLP using majority voting.
              </p>
            </div>
            <span
              style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                background: '#e2e8f0',
                color: '#475569',
                fontWeight: 600,
              }}
            >
              Experimental Consensus
            </span>
          </div>
        </div>
      )}

      {/* Patient-Friendly Interpretation & Guidance */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        {/* What this result means */}
        <div
          style={{
            padding: '1rem 1.15rem',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            boxShadow: 'var(--shadow-xs)',
          }}
        >
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}
          >
            <span style={{ color: 'var(--accent)', display: 'flex' }} aria-hidden="true">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </span>
            <strong style={{ fontSize: '0.95rem', color: 'var(--primary)' }}>
              What This Result Means
            </strong>
          </div>
          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
              margin: 0,
            }}
          >
            {isPositive
              ? 'This assessment reflects a statistical pattern associated with elevated risk in retrospective research data. It is an experimental decision-support estimate based solely on the measurements provided, not a clinical diagnosis or medical conclusion.'
              : 'The evaluated models did not detect elevated risk patterns in your submitted measurements relative to the training baseline. This is an informational indicator, not a definitive diagnosis or a guarantee against underlying conditions.'}
          </p>
        </div>

        {/* What to do next */}
        <div
          style={{
            padding: '1rem 1.15rem',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            boxShadow: 'var(--shadow-xs)',
          }}
        >
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}
          >
            <span style={{ color: 'var(--success)', display: 'flex' }} aria-hidden="true">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <line x1="19" y1="8" x2="19" y2="14" />
                <line x1="22" y1="11" x2="16" y2="11" />
              </svg>
            </span>
            <strong style={{ fontSize: '0.95rem', color: 'var(--primary)' }}>
              What to Do Next
            </strong>
          </div>
          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
              margin: 0,
            }}
          >
            Share this report with your qualified healthcare provider. A licensed clinician must
            evaluate these indicators in the context of your complete medical history, physical
            symptoms, and confirmatory laboratory tests. Do not start, stop, or alter any
            medications or treatments based solely on an automated AI risk score. If you experience
            acute symptoms, seek immediate emergency care.
          </p>
        </div>
      </div>

      {/* Primary Influential Factors */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '0.5rem',
            flexWrap: 'wrap',
            marginBottom: '0.25rem',
          }}
        >
          <h3 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--primary)' }}>
            Most Influential Health Factors
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            (SHAP &bull; Primary Model:{' '}
            {result.model_name === 'random_forest'
              ? 'Random Forest'
              : result.model_name === 'logistic_regression'
                ? 'Logistic Regression'
                : result.model_name}
            )
          </span>
        </div>
        <p className="hint" style={{ marginBottom: '1rem' }}>
          These feature contributions are mathematically computed using SHAP on the primary
          reference model (
          {result.model_name === 'random_forest' ? 'Random Forest' : 'Logistic Regression'}). They
          explain how this specific model reasoned, rather than the multi-model consensus.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {topFactors.map((item) => {
            const increases = item.contribution > 0
            const valStr = item.value !== null ? String(item.value) : 'Not provided (imputed)'
            return (
              <div
                key={item.feature}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius)',
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  boxShadow: 'var(--shadow-xs)',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <div>
                  <strong style={{ fontSize: '0.95rem', color: 'var(--text)' }}>
                    {item.label}
                  </strong>
                  <div
                    style={{
                      fontSize: '0.85rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.15rem',
                    }}
                  >
                    Entered value: <span style={{ fontWeight: 600 }}>{valStr}</span>
                    {item.imputed && (
                      <span
                        style={{ marginLeft: '0.5rem', color: 'var(--warn)', fontStyle: 'italic' }}
                      >
                        (estimated)
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      backgroundColor: increases ? '#fef3c7' : '#ecfdf5',
                      color: increases ? '#b45309' : '#047857',
                      border: `1px solid ${increases ? '#fde68a' : '#a7f3d0'}`,
                    }}
                  >
                    {increases ? 'Pushes toward elevated risk' : 'Pushes toward lower risk'}
                  </span>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                    Model impact: {item.contribution > 0 ? '+' : ''}
                    {item.contribution.toFixed(3)} ({result.shap.output_space})
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Warnings if any */}
      {result.warnings && result.warnings.length > 0 && (
        <div
          style={{
            marginBottom: '1.5rem',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius)',
            background: 'var(--warn-bg)',
            border: '1px solid var(--warn-border)',
          }}
        >
          <strong style={{ fontSize: '0.85rem', color: 'var(--warn)' }}>
            Assessment Limitations &amp; Notes:
          </strong>
          <ul
            style={{
              fontSize: '0.8rem',
              color: 'var(--warn)',
              marginTop: '0.25rem',
              paddingLeft: '1.25rem',
            }}
          >
            {result.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions: Download PDF and Reset */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '1.5rem',
        }}
      >
        {result.record_id && (
          <button
            type="button"
            className="primary"
            onClick={handleDownloadPdf}
            disabled={downloading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            {downloading ? 'Preparing PDF…' : 'Download Clinical Report (PDF)'}
          </button>
        )}

        <button type="button" className="secondary" onClick={onReset}>
          Start New Assessment
        </button>
      </div>

      {downloadError && (
        <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          {downloadError}
        </p>
      )}

      {/* Disclaimer */}
      <div
        style={{
          borderTop: '1px solid var(--border)',
          paddingTop: '1rem',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
        }}
      >
        <strong>Clinical Safety Notice:</strong> ClariDx provides AI-assisted clinical decision
        support for academic and educational reference only. It does not provide medical diagnoses
        or treatment plans. Predictions are based on historical retrospective research datasets and
        raw scores are uncalibrated. Always consult a board-certified physician or qualified
        healthcare provider regarding symptoms, test results, or medical decisions.
      </div>
    </div>
  )
}
