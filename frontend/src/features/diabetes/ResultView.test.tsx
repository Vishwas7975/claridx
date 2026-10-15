import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { diabetesFixture } from '../../test/fixtures'
import { makeDiabetesPrediction } from '../../test/prediction'
import { EXAMPLES } from './examples'
import { ResultView } from './ResultView'

describe('ResultView', () => {
  it('renders estimated probability of diabetes and decision threshold', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(screen.getByText('35.0%')).toBeInTheDocument()
    expect(screen.getByText(/estimated probability of diabetes/)).toBeInTheDocument()
    expect(screen.getByText(/at or above the decision threshold of 34%/)).toBeInTheDocument()
  })

  it('renders uncalibrated score note when calibrated is false', () => {
    render(<ResultView result={makeDiabetesPrediction({ calibrated: false })} />)
    expect(screen.getByText(/uncalibrated model output: treat it as a score/)).toBeInTheDocument()
  })

  it('moves focus to the result heading on mount', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(screen.getByRole('heading', { name: 'Result' })).toHaveFocus()
  })

  it('explicitly handles sensitivity: null without fabricating metrics', () => {
    render(<ResultView result={makeDiabetesPrediction({ sensitivity: null })} />)
    expect(screen.queryByText(/typical/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/positive_share/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/plausible/i)).not.toBeInTheDocument()
  })
})

describe('probability bar', () => {
  it('renders an accessible img role labelled with probability of diabetes', () => {
    render(<ResultView result={makeDiabetesPrediction({ probability: 0.35 })} />)
    expect(
      screen.getByRole('img', { name: /35\.0% estimated probability of diabetes/ }),
    ).toBeInTheDocument()
  })

  it('shows decision threshold in bar legend', () => {
    render(<ResultView result={makeDiabetesPrediction({ threshold: 0.34 })} />)
    expect(screen.getByText('Decision threshold: 34%')).toBeInTheDocument()
  })
})

describe('agreement section', () => {
  it('omits agreement section when agreement is null (Logistic Regression)', () => {
    render(<ResultView result={makeDiabetesPrediction({ agreement: null })} />)
    expect(screen.queryByText(/agreement/i)).not.toBeInTheDocument()
  })

  it('renders agreement section when agreement is present (Random Forest)', () => {
    render(
      <ResultView
        result={makeDiabetesPrediction({
          model_name: 'random_forest',
          agreement: {
            k: 3,
            rank_correlation: 0.85,
            top_k_overlap: 0.67,
            sign_agreement: 1.0,
          },
        })}
      />,
    )
    expect(
      screen.getByText(
        /SHAP vs LIME agreement \(top 3\): rank correlation 0\.85, overlap 67%, sign agreement 100%/,
      ),
    ).toBeInTheDocument()
  })

  it('shows an em dash when rank correlation is null in agreement', () => {
    render(
      <ResultView
        result={makeDiabetesPrediction({
          agreement: {
            k: 3,
            rank_correlation: null,
            top_k_overlap: 0.67,
            sign_agreement: 1.0,
          },
        })}
      />,
    )
    expect(screen.getByText(/rank correlation \u2014/)).toBeInTheDocument()
  })
})

describe('warnings and imputed features', () => {
  it('renders warnings list when warnings are returned', () => {
    const warnings = [
      'Cross-explainer agreement metrics are omitted for logistic regression.',
      'Age was entered as 21, which is at the lower bound.',
    ]
    render(<ResultView result={makeDiabetesPrediction({ warnings })} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Please note')).toBeInTheDocument()
    for (const w of warnings) {
      expect(screen.getByText(w)).toBeInTheDocument()
    }
  })

  it('renders imputed features information when imputed features exist', () => {
    render(
      <ResultView
        result={makeDiabetesPrediction({
          imputed_features: ['skin', 'insu'],
        })}
      />,
    )
    expect(screen.getByText(/Imputed features \(2\): skin, insu/)).toBeInTheDocument()
  })

  it('labels imputed contributions with (assumed) and applies contrib-row--imputed class', () => {
    const { container } = render(
      <ResultView
        result={makeDiabetesPrediction({
          shap: {
            method: 'shap',
            output_space: 'log_odds',
            base_value: -0.5,
            fidelity: null,
            low_confidence: false,
            contributions: [
              {
                feature: 'skin',
                label: 'Triceps skinfold thickness',
                value: null,
                imputed: true,
                contribution: 0.15,
              },
            ],
          },
        })}
      />,
    )
    expect(screen.getByText(/\(assumed\)/)).toBeInTheDocument()
    expect(container.querySelector('.contrib-row--imputed')).toBeInTheDocument()
  })
})

describe('contributions', () => {
  it('labels output space as log-odds for SHAP and probability for LIME', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(screen.getByText('Contributions in log-odds')).toBeInTheDocument()
    expect(screen.getByText('Contributions in probability')).toBeInTheDocument()
  })

  it('shows SHAP base value in log-odds', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(screen.getByText(/Base \(no input\): -0\.840 log-odds/)).toBeInTheDocument()
  })

  it('shows LIME local fit R²', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(screen.getByText(/Local fit R²: 0\.82/)).toBeInTheDocument()
  })

  it('shows low-confidence badge when LIME fidelity is low', () => {
    const base = makeDiabetesPrediction()
    render(
      <ResultView
        result={{
          ...base,
          lime: { ...base.lime, fidelity: 0.35, low_confidence: true },
        }}
      />,
    )
    expect(screen.getByText(/⚠ low local fit/)).toBeInTheDocument()
  })

  it('shows empty placeholder when contributions are empty', () => {
    const base = makeDiabetesPrediction()
    render(
      <ResultView
        result={{
          ...base,
          shap: { ...base.shap, contributions: [] },
          lime: { ...base.lime, contributions: [] },
        }}
      />,
    )
    expect(screen.getAllByText('No contributions available.')).toHaveLength(2)
  })

  it('formats unmeasured suspicious zeros using describeValue with specs', () => {
    const base = makeDiabetesPrediction()
    render(
      <ResultView
        result={{
          ...base,
          shap: {
            ...base.shap,
            contributions: [
              {
                feature: 'insu',
                label: '2-Hour serum insulin',
                value: 0,
                imputed: true,
                contribution: 0.05,
              },
            ],
          },
        }}
        specs={diabetesFixture.features}
      />,
    )
    expect(screen.getByText('unmeasured')).toBeInTheDocument()
  })
})

describe('metadata and disclaimer', () => {
  it('renders model name, version and disclaimer', () => {
    render(<ResultView result={makeDiabetesPrediction()} />)
    expect(
      screen.getByText(/Model: logistic regression · version diabetes-test/),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Research prototype for decision support and education only/),
    ).toBeInTheDocument()
  })
})

describe('examples', () => {
  it('has four defined examples with appropriate features', () => {
    expect(EXAMPLES).toHaveLength(4)
    const minimal = EXAMPLES.find((e) => e.id === 'minimal')
    expect(minimal).toBeDefined()
    expect(minimal!.values.preg).toBe(0)
    expect(Object.keys(minimal!.values)).toHaveLength(5)
  })
})
