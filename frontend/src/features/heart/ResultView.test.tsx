import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Sensitivity } from '../../api/types'
import { makePrediction } from '../../test/prediction'
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
