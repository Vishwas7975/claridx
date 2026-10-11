import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { json, mockApi } from '../../test/mockApi'
import { makePrediction } from '../../test/prediction'
import { EXAMPLES } from './examples'
import { PredictionPage } from './PredictionPage'

type User = ReturnType<typeof userEvent.setup>

function renderPage(): User {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <PredictionPage />
    </QueryClientProvider>,
  )
  return userEvent.setup()
}

async function analyseExample(user: User, index = 0) {
  await user.click(await screen.findByRole('button', { name: EXAMPLES[index].label }))
  await user.click(screen.getByRole('button', { name: 'Analyse' }))
}

describe('PredictionPage', () => {
  it('loads the form definitions from the API', async () => {
    mockApi()
    renderPage()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()
  })

  it('sends the entered measurements and shows the result', async () => {
    const calls = mockApi({ predictions: () => json(makePrediction()) })
    const user = renderPage()

    await analyseExample(user, 0)

    expect(await screen.findByText('61.5%')).toBeInTheDocument()
    expect(screen.getByText(/at or above the decision threshold of 50%/)).toBeInTheDocument()
    expect(screen.getByText(/uncalibrated model output/)).toBeInTheDocument()
    expect(calls).toHaveLength(1)
    expect(calls[0].body).toEqual({ model_name: 'random_forest', patient: EXAMPLES[0].values })
  })

  it('sends the selected model', async () => {
    const calls = mockApi({ predictions: () => json(makePrediction()) })
    const user = renderPage()

    await user.selectOptions(await screen.findByLabelText('Model'), 'logistic_regression')
    await analyseExample(user, 0)

    await screen.findByText('61.5%')
    expect(calls[0].body).toMatchObject({ model_name: 'logistic_regression' })
  })

  it('explains the effect of missing measurements', async () => {
    mockApi({
      predictions: () =>
        json(
          makePrediction({
            imputed_features: ['chol', 'ca', 'thal'],
            warnings: ['The result is uncertain because of missing measurements.'],
            sensitivity: {
              baseline_probability: 0.615,
              probability_min: 0.29,
              probability_max: 0.78,
              typical_low: 0.3,
              typical_high: 0.76,
              positive_share: 0.58,
              verdict_uncertain: true,
              patterns_used: 240,
              impacts: [],
              note: 'note',
            },
          }),
        ),
    })
    const user = renderPage()
    await analyseExample(user, 2)

    expect(await screen.findByText(/about 58% of those cases are positive/)).toBeInTheDocument()
    expect(screen.getByText(/typically 30% to 76%/)).toBeInTheDocument()
    expect(screen.getByText(/Because 3 measurements are missing/)).toBeInTheDocument()
    expect(
      screen.getByText('The result is uncertain because of missing measurements.'),
    ).toBeInTheDocument()
  })

  it('shows validation problems reported by the server next to the field', async () => {
    mockApi({
      predictions: () =>
        json(
          {
            detail: [
              {
                loc: ['body', 'patient', 'chol'],
                msg: 'Input should be less than or equal to 700',
                type: 'less_than_equal',
              },
            ],
          },
          422,
        ),
    })
    const user = renderPage()
    await analyseExample(user, 0)

    expect(await screen.findByText('Input should be less than or equal to 700')).toBeInTheDocument()
    expect(screen.getByText('The server rejected some of the values.')).toBeInTheDocument()
  })

  it('shows the server message when the models are not loaded (HTTP 503)', async () => {
    mockApi({ predictions: () => json({ detail: 'Prediction models are not loaded.' }, 503) })
    const user = renderPage()
    await analyseExample(user, 0)
    expect(await screen.findByText('Prediction models are not loaded.')).toBeInTheDocument()
  })

  it('tells the user when the server cannot be reached', async () => {
    mockApi({
      predictions: () => {
        throw new TypeError('Failed to fetch')
      },
    })
    const user = renderPage()
    await analyseExample(user, 0)
    expect(await screen.findByText(/cannot reach the server/i)).toBeInTheDocument()
  })

  it('removes the result as soon as an input changes', async () => {
    mockApi({ predictions: () => json(makePrediction()) })
    const user = renderPage()
    await analyseExample(user, 0)
    await screen.findByText('61.5%')

    await user.type(screen.getByLabelText('Age (years)'), '1')

    expect(screen.queryByText('61.5%')).not.toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()
  })

  it('offers a retry when the form definitions cannot be loaded', async () => {
    let attempt = 0
    mockApi({
      features: () =>
        attempt++ === 0
          ? json({ detail: 'Prediction models are not loaded.' }, 503)
          : json(heartFixtureFeatures()),
    })
    const user = renderPage()

    expect(await screen.findByText('Cannot load the form')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
  })
})

import { heartFixture } from '../../test/fixtures'

function heartFixtureFeatures() {
  return heartFixture.features
}
