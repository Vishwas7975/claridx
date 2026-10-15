import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EXAMPLES as heartExamples } from './features/heart/examples'
import { json, mockApi } from './test/mockApi'
import { makeDiabetesPrediction, makePrediction } from './test/prediction'
import App from './App'

type User = ReturnType<typeof userEvent.setup>

function renderApp(): User {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
  return userEvent.setup()
}

describe('App', () => {
  it('always shows the research-use banner, even while the form is still loading', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => {})),
    )
    render(
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>,
    )

    expect(screen.getByRole('heading', { name: 'ClariDx', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent(/not a medical device/i)
  })

  it('selects Heart Disease by default and renders the heart disease form', async () => {
    mockApi()
    renderApp()

    const heartBtn = screen.getByRole('button', { name: 'Heart Disease' })
    const diabetesBtn = screen.getByRole('button', { name: 'Diabetes' })

    expect(heartBtn).toHaveAttribute('aria-pressed', 'true')
    expect(diabetesBtn).toHaveAttribute('aria-pressed', 'false')

    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
    expect(screen.getByLabelText('Thallium stress test result')).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent(/not a medical device/i)
  })

  it('switches to Diabetes workflow when Diabetes is selected and preserves disclaimer', async () => {
    mockApi()
    const user = renderApp()

    await user.click(screen.getByRole('button', { name: 'Diabetes' }))

    const heartBtn = screen.getByRole('button', { name: 'Heart Disease' })
    const diabetesBtn = screen.getByRole('button', { name: 'Diabetes' })

    expect(diabetesBtn).toHaveAttribute('aria-pressed', 'true')
    expect(heartBtn).toHaveAttribute('aria-pressed', 'false')

    // Diabetes-specific inputs are shown
    expect(await screen.findByLabelText('Number of pregnancies')).toBeInTheDocument()
    expect(screen.getByLabelText('Plasma glucose concentration (mg/dL)')).toBeInTheDocument()
    expect(screen.getByLabelText('2-Hour serum insulin (mu U/ml)')).toBeInTheDocument()

    // Heart-specific inputs are absent
    expect(screen.queryByLabelText('Thallium stress test result')).not.toBeInTheDocument()

    // Permanent disclaimer is preserved
    expect(screen.getByRole('note')).toHaveTextContent(/not a medical device/i)
  })

  it('restores Heart Disease workflow when switching back from Diabetes', async () => {
    mockApi()
    const user = renderApp()

    await user.click(screen.getByRole('button', { name: 'Diabetes' }))
    expect(await screen.findByLabelText('Number of pregnancies')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Heart Disease' }))
    expect(await screen.findByLabelText('Thallium stress test result')).toBeInTheDocument()
    expect(screen.queryByLabelText('Number of pregnancies')).not.toBeInTheDocument()

    expect(screen.getByRole('note')).toHaveTextContent(/not a medical device/i)
  })

  it('does not leak predictions across workflows', async () => {
    mockApi({
      predictions: () => json(makePrediction({ probability: 0.615 })),
      diabetesPredictions: () => json(makeDiabetesPrediction()),
    })
    const user = renderApp()

    // Fill and submit heart prediction
    await user.click(await screen.findByRole('button', { name: heartExamples[0].label }))
    await user.click(screen.getByRole('button', { name: 'Analyse' }))
    expect(await screen.findByText('61.5%')).toBeInTheDocument()

    // Switch to Diabetes: result must not leak
    await user.click(screen.getByRole('button', { name: 'Diabetes' }))
    expect(await screen.findByLabelText('Number of pregnancies')).toBeInTheDocument()
    expect(screen.queryByText('61.5%')).not.toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()

    // Switch back to Heart: previous prediction should be cleared
    await user.click(screen.getByRole('button', { name: 'Heart Disease' }))
    expect(await screen.findByLabelText('Thallium stress test result')).toBeInTheDocument()
    expect(screen.queryByText('61.5%')).not.toBeInTheDocument()
    expect(screen.getByText(/result will appear here/i)).toBeInTheDocument()
  })
})
