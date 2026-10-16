import { useEffect, useRef } from 'react'
import type {
  Contribution,
  DiabetesAgreement,
  DiabetesPredictionResponse,
  Explanation,
  FeatureImpact,
  FeatureSpec,
  Sensitivity,
} from '../../api/types'
import { describeShare, describeValue, formatPercent, formatSigned, wholePercent } from './format'

function sensitivityText(sensitivity: Sensitivity, missing: number): string {
  const lead = sensitivity.verdict_uncertain ? 'The verdict is uncertain. ' : ''
  const noun = missing === 1 ? 'measurement is' : 'measurements are'
  const share = describeShare(sensitivity.positive_share)
  const portion = share === 'all' || share === 'none' ? share : `about ${share}`
  const low = wholePercent(sensitivity.typical_low)
  const high = wholePercent(sensitivity.typical_high)
  const patterns =
    sensitivity.patterns_used > 0
      ? ` (${sensitivity.patterns_used} background patterns evaluated)`
      : ''
  return (
    `${lead}Because ${missing} ${noun} missing, the result was re-computed with values real ` +
    `training patients have: ${portion} of those cases are positive, typically ${low} to ${high}${patterns}.`
  )
}

function SensitivityImpacts({ impacts }: { impacts: FeatureImpact[] }) {
  if (impacts.length === 0) return null
  return (
    <div className="sensitivity-impacts">
      <p className="sensitivity-impacts__title">
        Missing-feature impacts (typical range while varying each feature alone):
      </p>
      <ul className="sensitivity-impacts__list">
        {impacts.map((imp) => {
          const low = wholePercent(imp.typical_low)
          const high = wholePercent(imp.typical_high)
          return (
            <li key={imp.feature}>
              <strong>{imp.label}</strong>: typical range {low} to {high}
              {imp.can_flip && (
                <span className="badge badge--warn" role="status">
                  {' '}
                  ⚠ can alter verdict
                </span>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function ProbabilityBar({ probability, threshold }: { probability: number; threshold: number }) {
  const fillPct = Math.min(100, Math.max(0, probability * 100))
  const thresholdPct = Math.min(100, Math.max(0, threshold * 100))
  return (
    <div className="prob-bar-wrap">
      <div
        className="prob-bar"
        role="img"
        aria-label={`Probability bar: ${formatPercent(probability)} estimated probability of diabetes`}
      >
        <div className="prob-bar__fill" style={{ width: `${fillPct}%` }} />
      </div>
      <div
        className="prob-bar__threshold"
        style={{ left: `${thresholdPct}%` }}
        aria-hidden="true"
      />
      <div className="prob-bar__legend" aria-hidden="true">
        <span>0%</span>
        <span>Decision threshold: {formatPercent(threshold, 0)}</span>
        <span>100%</span>
      </div>
    </div>
  )
}

function ContributionRow({
  contribution: c,
  maxAbs,
  specsByName,
}: {
  contribution: Contribution
  maxAbs: number
  specsByName?: Map<string, FeatureSpec>
}) {
  const barPct = maxAbs > 0 ? (Math.abs(c.contribution) / maxAbs) * 100 : 0
  const isPos = c.contribution >= 0
  const spec = specsByName?.get(c.feature)
  return (
    <div className={`contrib-row${c.imputed ? ' contrib-row--imputed' : ''}`}>
      <div className="contrib-row__label">
        <span>
          {c.label}
          {c.imputed && <span className="contrib-row__assumed"> (assumed)</span>}
        </span>
        <span className="contrib-row__value">{describeValue(spec, c.value)}</span>
      </div>
      <div className="contrib-bar-wrap">
        <div className="contrib-bar-track">
          <div
            className={`contrib-bar ${isPos ? 'contrib-bar--pos' : 'contrib-bar--neg'}`}
            style={{ width: `${barPct}%` }}
          />
        </div>
        <span className="contrib-bar__signed">{formatSigned(c.contribution)}</span>
      </div>
    </div>
  )
}

function ContributionList({
  expl,
  specsByName,
}: {
  expl: Explanation
  specsByName?: Map<string, FeatureSpec>
}) {
  const maxAbs =
    expl.contributions.length > 0
      ? Math.max(...expl.contributions.map((c) => Math.abs(c.contribution)))
      : 1
  const spaceName = expl.output_space === 'probability' ? 'probability' : 'log-odds'
  return (
    <div className="explain-col">
      <p className="explain-col__title">{expl.method === 'shap' ? 'SHAP' : 'LIME'}</p>
      <p className="explain-col__space">Contributions in {spaceName}</p>
      {expl.contributions.length > 0 && (
        <p className="explain-col__legend">Dashed rows are assumptions, not measured inputs</p>
      )}
      {expl.contributions.length === 0 && (
        <p className="explain-empty">No contributions available.</p>
      )}
      {expl.contributions.map((c) => (
        <ContributionRow
          key={c.feature}
          contribution={c}
          maxAbs={maxAbs}
          specsByName={specsByName}
        />
      ))}
      {expl.method === 'shap' && expl.base_value !== null && (
        <p className="explain-base">
          Base (no input): {expl.base_value.toFixed(3)} {spaceName}
        </p>
      )}
      {expl.method === 'lime' && (expl.fidelity !== null || expl.low_confidence) && (
        <p className="explain-base">
          {expl.fidelity !== null && <>Local fit R²: {expl.fidelity.toFixed(2)}</>}
          {expl.low_confidence && (
            <span className="badge badge--warn" role="status">
              {' '}
              ⚠ low local fit
            </span>
          )}
        </p>
      )}
    </div>
  )
}

function AgreementSection({ agreement }: { agreement: DiabetesAgreement }) {
  const rho = agreement.rank_correlation !== null ? agreement.rank_correlation.toFixed(2) : '\u2014'
  return (
    <div className="agreement">
      <p>
        SHAP vs LIME agreement (top {agreement.k}): rank correlation {rho}, overlap{' '}
        {formatPercent(agreement.top_k_overlap, 0)}, sign agreement{' '}
        {formatPercent(agreement.sign_agreement, 0)}
      </p>
    </div>
  )
}

interface Props {
  result: DiabetesPredictionResponse
  specs?: FeatureSpec[]
}

export function ResultView({ result, specs }: Props) {
  const headingRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  const specsByName = specs ? new Map(specs.map((s) => [s.name, s])) : undefined
  const sensitivity = result.sensitivity ?? null

  return (
    <section className="panel" aria-labelledby="result-heading">
      <h2 id="result-heading" ref={headingRef} tabIndex={-1}>
        Result
      </h2>

      <p className="headline">
        <span className="figure">{formatPercent(result.probability)}</span> estimated probability of
        diabetes
      </p>
      <p>
        The estimate is {result.predicted_positive ? 'at or above' : 'below'} the decision threshold
        of {formatPercent(result.threshold, 0)}.
        {!result.calibrated &&
          ' It is an uncalibrated model output: treat it as a score, not a measured risk.'}
      </p>

      <ProbabilityBar probability={result.probability} threshold={result.threshold} />

      {sensitivity !== null && (
        <div className="sensitivity-wrap">
          <p className={sensitivity.verdict_uncertain ? 'sensitivity uncertain' : 'sensitivity'}>
            {sensitivity.verdict_uncertain && <span aria-hidden="true">⚠ </span>}
            {sensitivityText(sensitivity, result.imputed_features.length)}
          </p>
          <SensitivityImpacts impacts={sensitivity.impacts} />
        </div>
      )}

      {result.imputed_features.length > 0 && (
        <p className="hint">
          Imputed features ({result.imputed_features.length}): {result.imputed_features.join(', ')}
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

      <div className="explain-grid">
        <ContributionList expl={result.shap} specsByName={specsByName} />
        <ContributionList expl={result.lime} specsByName={specsByName} />
      </div>

      {result.agreement != null && <AgreementSection agreement={result.agreement} />}

      <p className="meta">
        Model: {result.model_name.replace('_', ' ')} &middot; version {result.model_version}
      </p>
      <p className="disclaimer">{result.disclaimer}</p>
    </section>
  )
}
