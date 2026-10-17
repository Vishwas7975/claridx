import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { diabetesFixture, diabetesModelsFixture } from '../../test/fixtures'
import { json, mockApi } from '../../test/mockApi'
import {
  makeDiabetesPrediction,
  makeDiabetesPredictionWithSensitivity,
  makeDiabetesSensitivity,
} from '../../test/prediction'
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
  it('loads the form definitions and models from the API', async () => {
    mockApi()
    renderPage()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()

    // Model options loaded from API
    const modelSelect = screen.getByLabelText('Model') as HTMLSelectElement
    expect(modelSelect.value).toBe('logistic_regression')
  })

  it('sends the entered measurements and shows the diabetes result', async () => {
    const calls = mockApi({ diabetesPredictions: () => json(makeDiabetesPrediction()) })
    const user = renderPage()

    await analyseExample(user, 0)

    expect(await screen.findByText('65.0%')).toBeInTheDocument()
    expect(screen.getByText(/estimated probability of diabetes/)).toBeInTheDocument()
    expect(screen.getByText(/at or above the decision threshold of 50%/)).toBeInTheDocument()
    expect(calls).toHaveLength(1)
    expect(calls[0].path).toBe('/api/v1/diabetes/predictions')
    expect(calls[0].body).toEqual({
      model_name: 'logistic_regression',
      patient: EXAMPLES[0].values,
    })
  })

  it('sends the selected model and displays agreement for random_forest', async () => {
    const calls = mockApi({
      diabetesPredictions: () =>
        json(
          makeDiabetesPrediction({
            model_name: 'random_forest',
            agreement: {
              k: 3,
              rank_correlation: 0.85,
              top_k_overlap: 0.67,
              sign_agreement: 1.0,
            },
          }),
        ),
    })
    const user = renderPage()

    await user.selectOptions(await screen.findByLabelText('Model'), 'random_forest')
    await analyseExample(user, 0)

    await screen.findByText('65.0%')
    expect(calls[0].body).toMatchObject({ model_name: 'random_forest' })
    expect(screen.getByText(/SHAP vs LIME agreement \(top 3\)/)).toBeInTheDocument()
  })

  it('omits agreement for logistic_regression where agreement is null', async () => {
    mockApi({
      diabetesPredictions: () =>
        json(
          makeDiabetesPrediction({
            model_name: 'logistic_regression',
            agreement: null,
          }),
        ),
    })
    const user = renderPage()
    await analyseExample(user, 0)

    await screen.findByText('65.0%')
    expect(screen.queryByText(/SHAP vs LIME agreement/)).not.toBeInTheDocument()
  })

  it('handles null sensitivity without crashing or fabricating text', async () => {
    mockApi({
      diabetesPredictions: () =>
        json(
          makeDiabetesPrediction({
            sensitivity: null,
          }),
        ),
    })
    const user = renderPage()
    await analyseExample(user, 0)

    await screen.findByText('65.0%')
    expect(screen.queryByText(/Because.*measurements are missing/)).not.toBeInTheDocument()
    expect(screen.queryByText(/background patterns evaluated/i)).not.toBeInTheDocument()
  })

  it('renders computed sensitivity and uncertain verdict when returned by the API', async () => {
    mockApi({
      diabetesPredictions: () => json(makeDiabetesPredictionWithSensitivity()),
    })
    const user = renderPage()
    await analyseExample(user, 3) // routine clinic example

    await screen.findByText('65.0%')
    expect(screen.getByText(/The verdict is uncertain/)).toBeInTheDocument()
    expect(screen.getByText(/Because 2 measurements are missing/)).toBeInTheDocument()
    expect(screen.getByText(/typically 28% to 58%/)).toBeInTheDocument()
    expect(screen.getByText(/120 background patterns evaluated/)).toBeInTheDocument()
    expect(screen.getByText('2-Hour serum insulin')).toBeInTheDocument()
  })

  it('renders stable computed sensitivity when verdict_uncertain is false', async () => {
    mockApi({
      diabetesPredictions: () =>
        json(
          makeDiabetesPrediction({
            imputed_features: ['skin', 'insu', 'pedi'],
            sensitivity: makeDiabetesSensitivity({
              verdict_uncertain: false,
              positive_share: 0,
              typical_low: 0.21,
              typical_high: 0.32,
              patterns_used: 324,
            }),
          }),
        ),
    })
    const user = renderPage()
    await analyseExample(user, 2) // minimal example

    await screen.findByText('65.0%')
    expect(screen.queryByText(/The verdict is uncertain/)).not.toBeInTheDocument()
    expect(screen.getByText(/Because 3 measurements are missing/)).toBeInTheDocument()
    expect(
      screen.getByText(/none of those cases are positive, typically 21% to 32%/),
    ).toBeInTheDocument()
    expect(screen.getByText(/324 background patterns evaluated/)).toBeInTheDocument()
  })

  it('shows warnings and imputed features returned by the prediction', async () => {
    mockApi({
      diabetesPredictions: () =>
        json(
          makeDiabetesPrediction({
            imputed_features: ['skin', 'insu'],
            warnings: [
              'Plasma glucose concentration was entered as 0; it was imputed using the training median.',
            ],
          }),
        ),
    })
    const user = renderPage()
    await analyseExample(user, 2) // minimal example

    expect(await screen.findByText(/Imputed features \(2\): skin, insu/)).toBeInTheDocument()
    expect(
      screen.getByText(
        'Plasma glucose concentration was entered as 0; it was imputed using the training median.',
      ),
    ).toBeInTheDocument()
  })

  it('shows validation problems reported by the server next to the field', async () => {
    mockApi({
      diabetesPredictions: () =>
        json(
          {
            detail: [
              {
                loc: ['body', 'patient', 'age'],
                msg: 'Input should be greater than or equal to 21',
                type: 'greater_than_equal',
              },
            ],
          },
          422,
        ),
    })
    const user = renderPage()
    await analyseExample(user, 0)

    expect(
      await screen.findByText('Input should be greater than or equal to 21'),
    ).toBeInTheDocument()
    expect(screen.getByText('The server rejected some of the values.')).toBeInTheDocument()
  })

  it('shows the server message when the models are not loaded (HTTP 503)', async () => {
    mockApi({
      diabetesPredictions: () => json({ detail: 'Prediction models are not loaded.' }, 503),
    })
    const user = renderPage()
    await analyseExample(user, 0)
    expect(await screen.findByText('Prediction models are not loaded.')).toBeInTheDocument()
  })

  it('tells the user when the server cannot be reached', async () => {
    mockApi({
      diabetesPredictions: () => {
        throw new TypeError('Failed to fetch')
      },
    })
    const user = renderPage()
    await analyseExample(user, 0)
    expect(await screen.findByText(/cannot reach the server/i)).toBeInTheDocument()
  })

  it('removes the result as soon as an input or model changes', async () => {
    mockApi({ diabetesPredictions: () => json(makeDiabetesPrediction()) })
    const user = renderPage()
    await analyseExample(user, 0)
    await screen.findByText('65.0%')

    // Invalidate on typing
    await user.type(screen.getByLabelText('Age (years)'), '1')
    expect(screen.queryByText('65.0%')).not.toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()

    // Analyse again
    await analyseExample(user, 0)
    await screen.findByText('65.0%')

    // Invalidate on model change
    await user.selectOptions(screen.getByLabelText('Model'), 'random_forest')
    expect(screen.queryByText('65.0%')).not.toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()
  })

  it('offers a retry when the form definitions cannot be loaded', async () => {
    let attempt = 0
    mockApi({
      diabetesFeatures: () =>
        attempt++ === 0
          ? json({ detail: 'Prediction models are not loaded.' }, 503)
          : json(diabetesFixture.features),
    })
    const user = renderPage()

    expect(await screen.findByText('Cannot load the form')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
  })

  it('offers a retry when the models list cannot be loaded', async () => {
    let attempt = 0
    mockApi({
      diabetesModels: () =>
        attempt++ === 0
          ? json({ detail: 'Cannot load models.' }, 503)
          : json(diabetesModelsFixture),
    })
    const user = renderPage()

    expect(await screen.findByText('Cannot load the form')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
  })
})
