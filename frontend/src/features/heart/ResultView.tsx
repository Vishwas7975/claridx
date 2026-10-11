import { useEffect, useRef } from 'react'
import type { PredictionResponse, Sensitivity } from '../../api/types'
import { describeShare, formatPercent, wholePercent } from './format'

function sensitivityText(sensitivity: Sensitivity, missing: number): string {
  const lead = sensitivity.verdict_uncertain ? 'The verdict is uncertain. ' : ''
  const noun = missing === 1 ? 'measurement is' : 'measurements are'
  const share = describeShare(sensitivity.positive_share)
  const portion = share === 'all' || share === 'none' ? share : `about ${share}`
  const low = wholePercent(sensitivity.typical_low)
  const high = wholePercent(sensitivity.typical_high)
  return (
    `${lead}Because ${missing} ${noun} missing, the result was re-computed with values real ` +
    `training patients have: ${portion} of those cases are positive, typically ${low} to ${high}.`
  )
}

export function ResultView({ result }: { result: PredictionResponse }) {
  // Move focus to the result so keyboard and screen-reader users land on it.
  const headingRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  const sensitivity = result.sensitivity ?? null

  return (
    <section className="panel" aria-labelledby="result-heading">
      <h2 id="result-heading" ref={headingRef} tabIndex={-1}>
        Result
      </h2>

      <p className="headline">
        <span className="figure">{formatPercent(result.probability)}</span> estimated probability of
        heart disease
      </p>
      <p>
        The estimate is {result.predicted_positive ? 'at or above' : 'below'} the decision threshold
        of {formatPercent(result.threshold, 0)}.
        {!result.calibrated &&
          ' It is an uncalibrated model output: treat it as a score, not a measured risk.'}
      </p>

      {sensitivity !== null && (
        <p className={sensitivity.verdict_uncertain ? 'sensitivity uncertain' : 'sensitivity'}>
          {sensitivityText(sensitivity, result.imputed_features.length)}
        </p>
      )}

      {result.warnings.length > 0 && (
        <div className="notice warn" role="alert">
          <strong>Please note</strong>
          <ul>
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="meta">
        Model: {result.model_name.replace('_', ' ')} &middot; version {result.model_version}
      </p>
      <p className="disclaimer">{result.disclaimer}</p>
    </section>
  )
}
