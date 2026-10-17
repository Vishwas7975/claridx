interface Props {
  condition: 'heart' | 'diabetes'
  modelName: string
  minMeasurements: number
  totalMeasurements: number
}

export function ResultsEmptyState({
  condition,
  modelName,
  minMeasurements,
  totalMeasurements,
}: Props) {
  const isDiabetes = condition === 'diabetes'
  const isLogisticRegression = modelName === 'logistic_regression'

  return (
    <div className="results-empty-state">
      <div className="empty-state-header">
        <div className="empty-state-icon" aria-hidden="true">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
        <div>
          <h3 className="empty-state-title">Decision Support &amp; Explainability Output</h3>
          <p className="placeholder">The result will appear here after you analyse a patient.</p>
        </div>
      </div>

      <div className="empty-state-divider" />

      <div className="empty-feature-list">
        <div className="empty-feature-item">
          <div className="empty-feature-marker" aria-hidden="true">
            1
          </div>
          <div className="empty-feature-content">
            <div className="empty-feature-title-row">
              <span className="empty-feature-title">Model Prediction &amp; Risk Estimate</span>
              <span className="badge badge-neutral">Decision Threshold</span>
            </div>
            <p className="empty-feature-desc">
              Estimates risk probability from entered patient measurements compared against the
              configured decision threshold. Note: tree ensemble models output uncalibrated scores.
            </p>
          </div>
        </div>

        <div className="empty-feature-item">
          <div className="empty-feature-marker" aria-hidden="true">
            2
          </div>
          <div className="empty-feature-content">
            <div className="empty-feature-title-row">
              <span className="empty-feature-title">SHAP &amp; LIME Feature Attributions</span>
              <span className="badge badge-accent">
                {isDiabetes && isLogisticRegression
                  ? 'Dual-Scale Explanations'
                  : 'Cross-Explainer Agreement'}
              </span>
            </div>
            <p className="empty-feature-desc">
              {isDiabetes && isLogisticRegression
                ? 'Linear SHAP (log-odds) and LIME surrogate (probability) show directional feature contributions. Explainer agreement is not computed across differing scales.'
                : 'Estimates local positive and negative feature contributions using SHAP values and a local linear surrogate model (LIME).'}
            </p>
          </div>
        </div>

        <div className="empty-feature-item">
          <div className="empty-feature-marker" aria-hidden="true">
            3
          </div>
          <div className="empty-feature-content">
            <div className="empty-feature-title-row">
              <span className="empty-feature-title">Missing-Data Sensitivity Analysis</span>
              <span className="badge badge-neutral">Empirical Scenarios</span>
            </div>
            <p className="empty-feature-desc">
              Evaluates empirical background patient patterns to check whether unmeasured values
              could alter the model output, highlighting clinical uncertainty.
            </p>
          </div>
        </div>
      </div>

      <div className="empty-state-footer">
        <span className="empty-state-tip">
          Enter at least {minMeasurements} of {totalMeasurements} measurements and click{' '}
          <strong>Analyse</strong>. Research prototype only — not for clinical diagnosis.
        </span>
      </div>
    </div>
  )
}
