import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { setAuthToken } from '../../api/client'
import type { UserProfile } from '../../api/types'
import App from '../../App'
import { json, mockApi } from '../../test/mockApi'
import { makePrediction } from '../../test/prediction'
import { EXAMPLES as heartExamples } from '../heart/examples'

const patientUser: UserProfile = {
  id: 10,
  email: 'alice@patient.test',
  full_name: 'Alice Patient',
  role: 'patient',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_login_at: '2026-01-01T00:00:00Z',
}

function renderApp() {
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

afterEach(() => {
  vi.unstubAllGlobals()
  sessionStorage.clear()
  setAuthToken(null)
})

describe('Patient Dashboard Workflow', () => {
  it('renders patient dashboard with overview and tabs for a patient user', async () => {
    mockApi({ authenticated: true, user: patientUser })
    renderApp()

    expect(screen.getByText('PATIENT')).toBeInTheDocument()
    expect(screen.getByText(/welcome, alice patient/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New Assessment' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /my history/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'My Account' })).toBeInTheDocument()
  })

  it('switches between tabs and shows account profile details', async () => {
    mockApi({ authenticated: true, user: patientUser })
    const user = renderApp()

    await user.click(screen.getByRole('button', { name: 'My Account' }))
    expect(screen.getByText('My Patient Account')).toBeInTheDocument()
    expect(screen.getByText('alice@patient.test')).toBeInTheDocument()
    expect(screen.getAllByText('Alice Patient').length).toBeGreaterThanOrEqual(1)
    expect(
      screen.getAllByRole('button', { name: /sign out of claridx/i }).length,
    ).toBeGreaterThanOrEqual(1)
  })

  it('shows empty state when patient has no past history records', async () => {
    mockApi({
      authenticated: true,
      user: patientUser,
      history: () => json({ items: [], total: 0, limit: 20, offset: 0 }),
    })
    const user = renderApp()

    await user.click(screen.getByRole('button', { name: /my history/i }))
    await waitFor(() => {
      expect(screen.getByText('No Prior Assessments Found')).toBeInTheDocument()
    })
  })

  it('displays history records and PDF download button', async () => {
    const mockRecord = {
      record_id: 'test-rec-1234-uuid',
      condition: 'heart',
      predicted_label: 'Elevated Risk',
      predicted_positive: true,
      probability: 0.82,
      threshold: 0.5,
      aggregation_method: 'majority_voting',
      model_version: 'heart-test',
      is_experimental: true,
      created_at: '2026-03-01T12:00:00Z',
      top_factors: [
        { feature: 'ca', label: 'Major vessels', value: 2, contribution: 0.35, imputed: false },
      ],
      model_results: [
        {
          model_name: 'random_forest',
          probability: 0.82,
          predicted_positive: true,
          threshold: 0.5,
          status: 'success',
        },
      ],
    }

    mockApi({
      authenticated: true,
      user: patientUser,
      history: () => json({ items: [mockRecord], total: 1, limit: 20, offset: 0 }),
    })
    const user = renderApp()

    await user.click(screen.getByRole('button', { name: /my history/i }))
    await waitFor(() => {
      expect(screen.getByText('Heart Disease Risk')).toBeInTheDocument()
      expect(screen.getByText('Elevated Risk')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'PDF Report' })).toBeInTheDocument()
    })
  })

  it('executes a heart assessment and renders simplified patient results', async () => {
    const samplePrediction = makePrediction({
      probability: 0.79,
      record_id: 'sample-pred-id-999',
      ensemble: {
        aggregation_method: 'majority_voting',
        is_experimental: true,
        predicted_positive: true,
        votes_positive: 4,
        votes_negative: 0,
        total_models_evaluated: 4,
        summary: 'Experimental majority voting: 4 elevated risk vote(s)',
        model_results: [
          {
            model_name: 'random_forest',
            probability: 0.79,
            predicted_positive: true,
            threshold: 0.5,
            status: 'success',
          },
          {
            model_name: 'logistic_regression',
            probability: 0.75,
            predicted_positive: true,
            threshold: 0.5,
            status: 'success',
          },
          {
            model_name: 'gradient_boosting',
            probability: 0.85,
            predicted_positive: true,
            threshold: 0.5,
            status: 'success',
          },
          {
            model_name: 'mlp',
            probability: 0.7,
            predicted_positive: true,
            threshold: 0.5,
            status: 'success',
          },
        ],
      },
    })

    mockApi({
      authenticated: true,
      user: patientUser,
      predictions: () => json(samplePrediction),
    })

    const user = renderApp()
    await user.click(screen.getByRole('button', { name: 'New Assessment' }))

    // Patient form does NOT have the Model dropdown
    expect(screen.queryByLabelText('Model')).not.toBeInTheDocument()

    // Fill measurements via reference patient
    const fillBtn = screen.getByRole('button', { name: heartExamples[0].label })
    await user.click(fillBtn)

    const predictBtn = screen.getByRole('button', { name: /analyse/i })
    expect(predictBtn).toBeEnabled()
    await user.click(predictBtn)

    // Results rendered in simplified patient view
    await screen.findByText('Assessment Results')
    expect(screen.getByText('Elevated Risk Detected')).toBeInTheDocument()
    expect(screen.getByText('Most Influential Health Factors')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /download clinical report/i })).toBeInTheDocument()
  })
})
