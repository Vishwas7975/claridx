import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, getAuthToken, setAuthToken } from '../../api/client'
import type { UserProfile } from '../../api/types'
import App from '../../App'
import { json, mockApi } from '../../test/mockApi'
import { makeDiabetesPrediction, makePrediction } from '../../test/prediction'
import { EXAMPLES as heartExamples } from '../heart/examples'
import { EXAMPLES as diabetesExamples } from '../diabetes/examples'

type User = ReturnType<typeof userEvent.setup>

function renderApp(): User {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <App initialView="login" />
    </QueryClientProvider>,
  )
  return userEvent.setup()
}

afterEach(() => {
  vi.unstubAllGlobals()
  sessionStorage.clear()
  setAuthToken(null)
})

describe('Authentication and RBAC Integration', () => {
  it('renders login form when user is not authenticated', () => {
    mockApi({ authenticated: false })
    renderApp()

    expect(
      screen.getByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Heart Disease' })).not.toBeInTheDocument()
  })

  it('successfully logs in, saves session, and displays doctor workspace', async () => {
    mockApi({
      authenticated: false,
      login: () => json({ access_token: 'secret-token-xyz', token_type: 'bearer' }),
      me: () =>
        json({
          id: 42,
          email: 'doctor.jones@claridx.test',
          full_name: 'Dr. Indiana Jones',
          role: 'doctor',
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
          last_login_at: '2026-01-01T00:00:00Z',
        } satisfies UserProfile),
    })

    const user = renderApp()

    await user.type(screen.getByLabelText(/email address/i), 'doctor.jones@claridx.test')
    await user.type(screen.getByLabelText(/password/i), 'SecurePass123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Dr. Indiana Jones')).toBeInTheDocument()
    expect(screen.getByText('DOCTOR')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Heart Disease' })).toBeInTheDocument()
    expect(sessionStorage.getItem('claridx_token')).toBe('secret-token-xyz')
    expect(getAuthToken()).toBe('secret-token-xyz')
  })

  it('handles invalid credentials with a generic, user-friendly error without leaking sensitive data', async () => {
    mockApi({
      authenticated: false,
      login: () => json({ detail: 'Incorrect email or password' }, 401),
    })

    const user = renderApp()

    await user.type(screen.getByLabelText(/email address/i), 'someone@claridx.test')
    await user.type(screen.getByLabelText(/password/i), 'WrongPassword123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/invalid email or password/i)
    // Verify no credential or token leakage
    expect(alert).not.toHaveTextContent('WrongPassword123!')
    expect(document.body.textContent).not.toContain('WrongPassword123!')
    expect(sessionStorage.getItem('claridx_token')).toBeNull()
  })

  it('handles inactive accounts gracefully without exposing internal details', async () => {
    mockApi({
      authenticated: false,
      login: () => json({ detail: 'Inactive user account' }, 403),
    })

    const user = renderApp()

    await user.type(screen.getByLabelText(/email address/i), 'inactive@claridx.test')
    await user.type(screen.getByLabelText(/password/i), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/account is not authorized or is inactive/i)
  })

  it('handles network or server failure gracefully', async () => {
    mockApi({
      authenticated: false,
      login: () => json({ detail: 'Internal Server Error' }, 500),
    })

    const user = renderApp()

    await user.type(screen.getByLabelText(/email address/i), 'doctor@claridx.test')
    await user.type(screen.getByLabelText(/password/i), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/unable to sign in/i)
  })

  it('prevents repeated submissions while login is in progress', async () => {
    let resolveLogin: (res: Response) => void = () => {}
    const loginPromise = new Promise<Response>((resolve) => {
      resolveLogin = resolve
    })

    mockApi({
      authenticated: false,
      login: () => loginPromise,
      me: () =>
        json({
          id: 1,
          email: 'doc@claridx.test',
          full_name: 'Dr. Physician',
          role: 'doctor',
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
          last_login_at: null,
        } satisfies UserProfile),
    })

    const user = renderApp()

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitBtn = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'doc@claridx.test')
    await user.type(passwordInput, 'Password123!')
    await user.click(submitBtn)

    expect(submitBtn).toBeDisabled()
    expect(submitBtn).toHaveTextContent(/signing in/i)
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()

    // Resolve login request
    resolveLogin(json({ access_token: 'new-token-123', token_type: 'bearer' }))

    expect(await screen.findByText('Dr. Physician')).toBeInTheDocument()
  })

  it('attaches bearer token to prediction requests', async () => {
    const calls = mockApi({
      authenticated: true,
      predictions: () => json(makePrediction({ probability: 0.55 })),
    })

    const user = renderApp()

    await user.click(await screen.findByRole('button', { name: heartExamples[0].label }))
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(await screen.findByText('55.0%')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
    expect(calls[0].authHeader).toBe('Bearer mock-test-token')
  })

  it('attaches bearer token to diabetes prediction requests', async () => {
    const calls = mockApi({
      authenticated: true,
      diabetesPredictions: () => json(makeDiabetesPrediction({ probability: 0.65 })),
    })

    const user = renderApp()

    await user.click(screen.getByRole('button', { name: 'Diabetes' }))
    await user.click(await screen.findByRole('button', { name: diabetesExamples[0].label }))
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(await screen.findByText('65.0%')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
    expect(calls[0].authHeader).toBe('Bearer mock-test-token')
  })

  it('ensures public metadata endpoints continue to work without a token', async () => {
    setAuthToken(null)
    const seenAuth: (string | null)[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (request: Request) => {
        seenAuth.push(request.headers.get('Authorization'))
        return json([])
      }),
    )

    const { data } = await api.GET('/api/v1/heart/features')
    expect(data).toEqual([])
    expect(seenAuth).toHaveLength(1)
    expect(seenAuth[0]).toBeNull()
  })

  it('logs out and clears session state when session expires (401)', async () => {
    mockApi({
      authenticated: true,
      predictions: () => json({ detail: 'Token has expired' }, 401),
    })

    const user = renderApp()

    expect(await screen.findByText('Dr. Test Physician')).toBeInTheDocument()

    // Try submitting prediction, which triggers 401
    await user.click(await screen.findByRole('button', { name: heartExamples[0].label }))
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    // User is logged out and returned to login screen
    expect(
      await screen.findByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
    ).toBeInTheDocument()
    expect(sessionStorage.getItem('claridx_token')).toBeNull()
    expect(getAuthToken()).toBeNull()
  })

  it('handles 403 forbidden without session destruction', async () => {
    mockApi({
      authenticated: true,
      predictions: () =>
        json({ detail: 'Access denied. Prediction endpoints require DOCTOR or ADMIN role.' }, 403),
    })

    const user = renderApp()

    expect(await screen.findByText('Dr. Test Physician')).toBeInTheDocument()

    await user.click(await screen.findByRole('button', { name: heartExamples[0].label }))
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(await screen.findByText(/Access denied/i)).toBeInTheDocument()
    // Session is still active
    expect(screen.getByText('Dr. Test Physician')).toBeInTheDocument()
  })

  it('displays prediction workflow for ADMIN user', async () => {
    mockApi({
      authenticated: true,
      user: {
        id: 99,
        email: 'admin@claridx.test',
        full_name: 'System Admin',
        role: 'admin',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        last_login_at: '2026-01-01T00:00:00Z',
      },
    })

    renderApp()

    expect(await screen.findByText('System Admin')).toBeInTheDocument()
    expect(screen.getByText('ADMIN')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Analyse' })).toBeInTheDocument()
    expect(screen.queryByRole('status', { name: /researcher access/i })).not.toBeInTheDocument()
  })

  it('displays prediction workflow for DOCTOR user', async () => {
    mockApi({
      authenticated: true,
      user: {
        id: 10,
        email: 'doctor@claridx.test',
        full_name: 'Dr. Sarah Connor',
        role: 'doctor',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        last_login_at: '2026-01-01T00:00:00Z',
      },
    })

    renderApp()

    expect(await screen.findByText('Dr. Sarah Connor')).toBeInTheDocument()
    expect(screen.getByText('DOCTOR')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Analyse' })).toBeInTheDocument()
  })

  it('restricts RESEARCHER user from prediction action while preserving metadata access', async () => {
    mockApi({
      authenticated: true,
      user: {
        id: 20,
        email: 'researcher@claridx.test',
        full_name: 'Dr. Researcher Roy',
        role: 'researcher',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        last_login_at: '2026-01-01T00:00:00Z',
      },
    })

    renderApp()

    expect(await screen.findByText('Dr. Researcher Roy')).toBeInTheDocument()
    expect(screen.getByText('RESEARCHER')).toBeInTheDocument()

    // Researcher notice is displayed
    expect(screen.getByText(/researcher access/i)).toBeInTheDocument()

    // Form inputs and condition tabs are accessible
    expect(await screen.findByLabelText('Age (years)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Diabetes' })).toBeInTheDocument()

    // Crucial requirement: Analyse action is NOT presented to researcher!
    expect(screen.queryByRole('button', { name: 'Analyse' })).not.toBeInTheDocument()
    expect(
      screen.getByText(/prediction generation is restricted to doctor and admin accounts/i),
    ).toBeInTheDocument()
  })

  it('logs out when Sign out button is clicked', async () => {
    mockApi({ authenticated: true })
    const user = renderApp()

    expect(await screen.findByText('Dr. Test Physician')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /sign out/i }))

    expect(
      await screen.findByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
    ).toBeInTheDocument()
    expect(sessionStorage.getItem('claridx_token')).toBeNull()
    expect(getAuthToken()).toBeNull()
    expect(screen.queryByText('Dr. Test Physician')).not.toBeInTheDocument()
  })
})
