import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { HistoryRecord } from '../../api/types'
import { useAuth } from '../auth/AuthContext'

interface Props {
  onStartAssessment: () => void
}

interface FactorItem {
  feature?: string
  label?: string
  value?: string | number | null
  contribution: number
  imputed?: boolean
}

interface ModelResultItem {
  model_name: string
  probability?: number | null
  predicted_positive?: boolean | null
  threshold?: number
  status?: string
}

function formatAssessmentDate(isoString: string): { local: string; utc: string } {
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return { local: isoString, utc: '' }
  const local = d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  let tzName: string
  try {
    tzName = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local'
  } catch {
    tzName = 'Local'
  }
  const utc = d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC'
  return { local: `${local} (${tzName})`, utc }
}

export function PatientHistoryView({ onStartAssessment }: Props) {
  const { token } = useAuth()
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const historyQuery = useQuery({
    queryKey: ['patient-history', token],
    staleTime: 60000,
    queryFn: async () => {
      const res = await fetch('/api/v1/history?limit=50', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (!res.ok) {
        throw new Error(`Failed to load history (${res.status})`)
      }
      const data = await res.json()
      return (data.items || []) as HistoryRecord[]
    },
    enabled: Boolean(token),
  })

  const loading = historyQuery.isPending
  const error = historyQuery.isError ? 'Unable to load assessment history. Please try again.' : null
  const records = historyQuery.data || []

  async function handleDownload(record: HistoryRecord) {
    setDownloadingId(record.record_id)
    try {
      const res = await fetch(`/api/v1/history/${record.record_id}/pdf`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (!res.ok) throw new Error('Failed to download report')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `claridx_${record.condition}_${record.record_id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Could not download PDF. Please try again.')
    } finally {
      setDownloadingId(null)
    }
  }

  if (loading) {
    return (
      <div className="panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <p className="hint">Loading your assessment history…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>
        <button type="button" className="secondary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    )
  }

  if (records.length === 0) {
    return (
      <div className="panel" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
        <div
          style={{ width: '48px', height: '48px', margin: '0 auto 1rem', color: 'var(--accent)' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.5L19 7.5V19a2 2 0 0 1-2 2z" />
          </svg>
        </div>
        <h3 style={{ fontSize: '1.25rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>
          No Prior Assessments Found
        </h3>
        <p className="hint" style={{ maxWidth: '420px', margin: '0 auto 1.5rem' }}>
          You have not completed any health risk evaluations yet. Start a new assessment to see your
          explainable results here.
        </p>
        <button type="button" className="primary" onClick={onStartAssessment}>
          Start New Assessment
        </button>
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="panel-header" style={{ marginBottom: '1.25rem' }}>
        <h2>My Assessment History</h2>
        <p className="hint">View and download your past clinical decision-support reports.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {records.map((rec) => {
          const isPos = rec.predicted_positive
          const { local: localDateStr, utc: utcDateStr } = formatAssessmentDate(rec.created_at)
          const isExpanded = expandedId === rec.record_id

          return (
            <div
              key={rec.record_id}
              style={{
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '1.25rem',
                background: 'var(--surface)',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                <div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.35rem',
                    }}
                  >
                    <strong style={{ fontSize: '1.05rem', color: 'var(--primary)' }}>
                      {rec.condition === 'heart' ? 'Heart Disease Risk' : 'Type 2 Diabetes Risk'}
                    </strong>
                    <span
                      style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: isPos ? 'var(--warn-bg)' : 'var(--success-bg)',
                        color: isPos ? 'var(--warn)' : 'var(--success)',
                        border: `1px solid ${isPos ? 'var(--warn-border)' : 'var(--success-border)'}`,
                      }}
                    >
                      {isPos ? 'Elevated Risk' : 'Lower Risk'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Assessment Date:{' '}
                    <strong style={{ color: 'var(--text)' }}>{localDateStr}</strong>
                    {utcDateStr && (
                      <span
                        style={{ fontSize: '0.78rem', color: 'var(--muted)', marginLeft: '0.4rem' }}
                      >
                        [{utcDateStr}]
                      </span>
                    )}{' '}
                    &bull; Method: {rec.aggregation_method}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button
                    type="button"
                    className="secondary sm"
                    onClick={() => setExpandedId(isExpanded ? null : rec.record_id)}
                  >
                    {isExpanded ? 'Hide Details' : 'View Details'}
                  </button>
                  <button
                    type="button"
                    className="primary sm"
                    onClick={() => handleDownload(rec)}
                    disabled={downloadingId === rec.record_id}
                  >
                    {downloadingId === rec.record_id ? 'Downloading…' : 'PDF Report'}
                  </button>
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div
                  style={{
                    marginTop: '1rem',
                    paddingTop: '1rem',
                    borderTop: '1px solid var(--border)',
                  }}
                >
                  {rec.top_factors && rec.top_factors.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ fontSize: '0.9rem', color: 'var(--primary)' }}>
                        Top Influential Factors:
                      </strong>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                          gap: '0.5rem',
                          marginTop: '0.5rem',
                        }}
                      >
                        {(rec.top_factors as unknown as FactorItem[])
                          .slice(0, 4)
                          .map((tf, i: number) => (
                            <div
                              key={i}
                              style={{
                                padding: '0.5rem 0.75rem',
                                background: 'var(--surface-raised)',
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.8rem',
                              }}
                            >
                              <strong>{tf.label || tf.feature}</strong>: {tf.value ?? 'N/A'}{' '}
                              <span
                                style={{
                                  color: tf.contribution > 0 ? 'var(--warn)' : 'var(--success)',
                                  fontWeight: 600,
                                }}
                              >
                                ({tf.contribution > 0 ? '+' : ''}
                                {Number(tf.contribution).toFixed(3)})
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {rec.model_results && (
                    <div>
                      <strong style={{ fontSize: '0.9rem', color: 'var(--primary)' }}>
                        Four-Model Breakdown:
                      </strong>
                      <div
                        style={{
                          display: 'flex',
                          gap: '0.75rem',
                          flexWrap: 'wrap',
                          marginTop: '0.5rem',
                        }}
                      >
                        {(rec.model_results as unknown as ModelResultItem[]).map(
                          (mr, idx: number) => (
                            <div
                              key={idx}
                              style={{
                                padding: '0.4rem 0.75rem',
                                background: 'var(--surface-raised)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                fontSize: '0.78rem',
                              }}
                            >
                              <strong>{mr.model_name}</strong>:{' '}
                              {mr.status === 'success'
                                ? `${mr.predicted_positive ? 'Elevated' : 'Lower'}${mr.probability != null ? ` (${(mr.probability * 100).toFixed(0)}%)` : ''}`
                                : 'Failed'}
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
