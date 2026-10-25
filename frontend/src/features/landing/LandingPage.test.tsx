import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { setAuthToken } from '../../api/client'
import App from '../../App'
import { mockApi } from '../../test/mockApi'

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
  localStorage.clear()
  setAuthToken(null)
})

describe('ClariDx Public Landing Page & Visual Modernization', () => {
  it('renders landing page by default for unauthenticated visitors', () => {
    mockApi({ authenticated: false })
    renderApp()

    // 1. Branding
    expect(screen.getByRole('heading', { name: 'ClariDx', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByText('Clinical AI you can see through').length).toBeGreaterThanOrEqual(1)

    // 2. Navigation Actions
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Get Started' })).toBeInTheDocument()

    // 3. Hero Section
    expect(
      screen.getByRole('heading', {
        name: 'Clinical AI Decision Support You Can See Through',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start Patient Assessment' })).toBeInTheDocument()

    // 4. Interactive Live Clinical Preview Card
    expect(screen.getByText('Interactive Assessment Preview')).toBeInTheDocument()
    expect(screen.getByText('4 of 4 Models Agree')).toBeInTheDocument()
    expect(screen.getByText('Multi-Model Ensemble')).toBeInTheDocument()
    expect(screen.getByText(/Primary Model SHAP Attributions/)).toBeInTheDocument()

    // 5. Four-Step Pipeline Section
    expect(screen.getByText('Standardized Clinical Inputs')).toBeInTheDocument()
    expect(screen.getByText('4-Model Concurrent Execution')).toBeInTheDocument()
    expect(screen.getByText('Deterministic Majority Voting')).toBeInTheDocument()
    expect(screen.getByText(/SHAP Attribution & PDF Export/)).toBeInTheDocument()

    // 6. Supported Conditions
    expect(screen.getAllByText('Heart Disease Risk').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Diabetes Risk Analysis').length).toBeGreaterThanOrEqual(1)

    // 7. Explainability & Sensitivity
    expect(screen.getByText('SHAP Feature Attribution')).toBeInTheDocument()
    expect(screen.getByText('Single-Model Attribution Honesty')).toBeInTheDocument()
    expect(screen.getByText('Missing-Data Sensitivity Analysis')).toBeInTheDocument()

    // 8. Auditable History & PDF Reports
    expect(screen.getByText('Auditable Assessment History & PDF Reports')).toBeInTheDocument()

    // 9. Safety Disclosure
    expect(
      screen.getByText(/Research prototype for decision support and education only/i),
    ).toBeInTheDocument()

    // 10. Professional Footer
    expect(
      screen.getByText(
        /Transparent machine learning decision support engineered for educational transparency/i,
      ),
    ).toBeInTheDocument()
  })

  it('navigates from landing page to sign in and back to home', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    // Click Sign In in navbar
    const signInBtn = screen.getByRole('button', { name: 'Sign In' })
    await user.click(signInBtn)

    // Verify Sign In screen is rendered
    expect(
      screen.getByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
    ).toBeInTheDocument()

    // Click "Back to Home" in top bar
    const backBtn = screen.getByRole('button', { name: 'Back to Home' })
    await user.click(backBtn)

    // Verify returned to Landing Page
    expect(
      screen.getByRole('heading', {
        name: 'Clinical AI Decision Support You Can See Through',
      }),
    ).toBeInTheDocument()
  })

  it('navigates from landing page hero CTA to registration and back', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    // Click "Get Started" in navbar
    const getStartedBtn = screen.getByRole('button', { name: 'Get Started' })
    await user.click(getStartedBtn)

    // Verify registration form is displayed
    expect(
      screen.getByRole('heading', { name: 'Create Patient Account', level: 2 }),
    ).toBeInTheDocument()

    // Click "Back to Home" in top bar
    const backBtn = screen.getByRole('button', { name: 'Back to Home' })
    await user.click(backBtn)

    // Verify returned to Landing Page
    expect(screen.getByText('Interactive Assessment Preview')).toBeInTheDocument()
  })

  it('toggles light and dark themes using the theme toggle button', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    // Default theme is dark
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    const toggleBtn = screen.getByRole('button', { name: /switch to light mode/i })
    expect(toggleBtn).toBeInTheDocument()

    // Toggle to light mode
    await user.click(toggleBtn)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(localStorage.getItem('claridx_theme')).toBe('light')

    // Toggle back to dark mode
    const toggleBackBtn = screen.getByRole('button', { name: /switch to dark mode/i })
    await user.click(toggleBackBtn)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem('claridx_theme')).toBe('dark')
  })

  it('switches preview condition tabs on the interactive clinical preview card', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    // Default preview shows heart probability and factors
    expect(screen.getByText('78.4%')).toBeInTheDocument()
    expect(screen.getByText('Thallium stress test result (7.0)')).toBeInTheDocument()

    // Switch to diabetes preview tab inside the preview mockup
    const diabetesTab = screen
      .getAllByRole('button', { name: 'Diabetes' })
      .find((btn) => btn.classList.contains('mockup-tab'))
    expect(diabetesTab).toBeDefined()
    if (diabetesTab) {
      await user.click(diabetesTab)
    }

    await waitFor(() => {
      expect(screen.getByText('74.2%')).toBeInTheDocument()
      expect(screen.getByText('Plasma glucose (168 mg/dL)')).toBeInTheDocument()
    })
  })
})
