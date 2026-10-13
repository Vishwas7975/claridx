import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Sensitivity } from '../../api/types'
import { makePrediction } from '../../test/prediction'
import { EXAMPLES } from './examples'
import { ResultView } from './ResultView'

function makeSensitivity(overrides: Partial<Sensitivity> = {}): Sensitivity {
  return {
    baseline_probability: 0.615,
    probability_min: 0.58,
    probability_max: 0.996,
    typical_low: 0.59,
    typical_high: 0.996,
    positive_share: 1,
    verdict_uncertain: false,
    patterns_used: 240,
    impacts: [],
    note: 'note',
    ...overrides,
  }
}

const MISSING_THREE = ['chol', 'ca', 'thal']

describe('ResultView', () => {
  it('says "all" and does not round a near-certain range up to 100%', () => {
    render(
      <ResultView
        result={makePrediction({ imputed_features: MISSING_THREE, sensitivity: makeSensitivity() })}
      />,
    )
    expect(
      screen.getByText(/all of those cases are positive, typically 59% to 99%/),
    ).toBeInTheDocument()
    expect(screen.queryByText(/The verdict is uncertain/)).not.toBeInTheDocument()
  })

  it('leads with "The verdict is uncertain" when plausible cases disagree', () => {
    const sensitivity = makeSensitivity({
      positive_share: 0.58,
      verdict_uncertain: true,
      typical_low: 0.3,
      typical_high: 0.76,
    })
    render(<ResultView result={makePrediction({ imputed_features: MISSING_THREE, sensitivity })} />)
    expect(
      screen.getByText(
        /The verdict is uncertain\. Because 3 measurements are missing.*about 58% of those cases are positive, typically 30% to 76%/,
      ),
    ).toBeInTheDocument()
  })

  it('shows no missing-data paragraph when every measurement was provided', () => {
    render(<ResultView result={makePrediction()} />)
    expect(screen.queryByText(/Because/)).not.toBeInTheDocument()
  })

  it('moves focus to the result heading', () => {
    render(<ResultView result={makePrediction()} />)
    expect(screen.getByRole('heading', { name: 'Result' })).toHaveFocus()
  })
})

describe('probability bar', () => {
  it('renders an accessible img role labelled with the probability', () => {
    render(<ResultView result={makePrediction({ probability: 0.615 })} />)
    expect(
      screen.getByRole('img', { name: /61\.5% estimated probability of heart disease/ }),
    ).toBeInTheDocument()
  })

  it('shows the decision threshold label in the bar legend', () => {
    render(<ResultView result={makePrediction()} />)
    expect(screen.getByText('Decision threshold: 50%')).toBeInTheDocument()
  })
})

describe('contribution lists', () => {
  it('labels the output space for each method', () => {
    render(<ResultView result={makePrediction()} />)
    // Both SHAP and LIME use output_space 'probability' in the fixture → 2 elements
    expect(screen.getAllByText('Contributions in probability')).toHaveLength(2)
  })

  it('shows "Contributions in log-odds" when an explanation uses log-odds', () => {
    const base = makePrediction()
    const pred = makePrediction({
      shap: { ...base.shap, output_space: 'log_odds' },
    })
    render(<ResultView result={pred} />)
    expect(screen.getByText('Contributions in log-odds')).toBeInTheDocument()
  })

  it('shows the SHAP base value with its output space', () => {
    render(<ResultView result={makePrediction()} />)
    expect(screen.getByText(/Base \(no input\): 0\.463 probability/)).toBeInTheDocument()
  })

  it('labels imputed contributions as "(assumed)"', () => {
    render(<ResultView result={makePrediction()} />)
    // ca is imputed in both SHAP and LIME columns in the fixture
    expect(screen.getAllByText(/\(assumed\)/).length).toBeGreaterThanOrEqual(2)
  })

  it('applies the contrib-row--imputed class to assumed rows', () => {
    const { container } = render(<ResultView result={makePrediction()} />)
    expect(container.querySelectorAll('.contrib-row--imputed').length).toBeGreaterThanOrEqual(2)
  })

  it('shows "not provided" for null contribution values', () => {
    render(<ResultView result={makePrediction()} />)
    // ca has value: null in both columns
    expect(screen.getAllByText('not provided').length).toBeGreaterThanOrEqual(2)
  })

  it('shows a placeholder when contribution lists are empty', () => {
    const base = makePrediction()
    const pred = makePrediction({
      shap: { ...base.shap, contributions: [] },
      lime: { ...base.lime, contributions: [] },
    })
    render(<ResultView result={pred} />)
    expect(screen.getAllByText('No contributions available.')).toHaveLength(2)
  })

  it('shows LIME local fit R²', () => {
    render(<ResultView result={makePrediction()} />)
    expect(screen.getByText(/Local fit R²: 0\.75/)).toBeInTheDocument()
  })

  it('shows the low-confidence badge when LIME fit is weak', () => {
    const base = makePrediction()
    const pred = makePrediction({
      lime: { ...base.lime, fidelity: 0.4, low_confidence: true },
    })
    render(<ResultView result={pred} />)
    expect(screen.getByText(/⚠ low local fit/)).toBeInTheDocument()
  })
})

describe('agreement section', () => {
  it('shows rank correlation, overlap and sign agreement', () => {
    render(<ResultView result={makePrediction()} />)
    expect(
      screen.getByText(/rank correlation 0\.90.*overlap 100%.*sign agreement 100%/),
    ).toBeInTheDocument()
  })

  it('shows an em dash when rank correlation is null', () => {
    const base = makePrediction()
    const pred = makePrediction({
      agreement: { ...base.agreement, rank_correlation: null },
    })
    render(<ResultView result={pred} />)
    expect(screen.getByText(/rank correlation \u2014/)).toBeInTheDocument()
  })
})

describe('fourth example', () => {
  it('includes an uncertain-verdict example with the four specified fields absent and at least 7 provided', () => {
    const uncertain = EXAMPLES.find((e) => e.id === 'uncertain')
    expect(uncertain).toBeDefined()
    const keys = Object.keys(uncertain!.values)
    expect(keys).not.toContain('thal')
    expect(keys).not.toContain('ca')
    expect(keys).not.toContain('cp')
    expect(keys).not.toContain('slope')
    expect(keys.length).toBeGreaterThanOrEqual(7)
  })
})
