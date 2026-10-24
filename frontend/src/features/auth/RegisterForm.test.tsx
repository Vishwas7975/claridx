import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { setAuthToken } from '../../api/client'
import App from '../../App'
import { json, mockApi } from '../../test/mockApi'

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

describe('Patient Registration Flow', () => {
  it('navigates from login to registration form and back', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    const createAccountLink = screen.getByRole('link', { name: /create an account/i })
    expect(createAccountLink).toBeInTheDocument()
    await user.click(createAccountLink)

    expect(
      screen.getByRole('heading', { name: 'Create Patient Account', level: 2 }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^confirm password$/i)).toBeInTheDocument()

    const signInLink = screen.getByRole('link', { name: /sign in/i })
    await user.click(signInLink)
    expect(
      screen.getByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
    ).toBeInTheDocument()
  })

  it('toggles password and confirm password visibility independently', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    await user.click(screen.getByRole('link', { name: /create an account/i }))

    const passwordInput = screen.getByLabelText(/^password/i) as HTMLInputElement
    const confirmPasswordInput = screen.getByLabelText(/^confirm password$/i) as HTMLInputElement

    expect(passwordInput.type).toBe('password')
    expect(confirmPasswordInput.type).toBe('password')

    const togglePasswordBtn = screen.getByRole('button', { name: /show password/i })
    const toggleConfirmBtn = screen.getByRole('button', { name: /show confirm password/i })

    // Click toggle on password only
    await user.click(togglePasswordBtn)
    expect(passwordInput.type).toBe('text')
    expect(confirmPasswordInput.type).toBe('password')
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument()

    // Click toggle on confirm password only
    await user.click(toggleConfirmBtn)
    expect(passwordInput.type).toBe('text')
    expect(confirmPasswordInput.type).toBe('text')
    expect(screen.getByRole('button', { name: /hide confirm password/i })).toBeInTheDocument()

    // Toggle back password
    await user.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput.type).toBe('password')
    expect(confirmPasswordInput.type).toBe('text')
  })

  it('validates password length and matching passwords', async () => {
    mockApi({ authenticated: false })
    const user = renderApp()

    await user.click(screen.getByRole('link', { name: /create an account/i }))

    await user.type(screen.getByLabelText(/full name/i), 'Jane Doe')
    await user.type(screen.getByLabelText(/^email address/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'pass')
    await user.type(screen.getByLabelText(/^confirm password$/i), 'pass')

    // Submit button is disabled because password < 8
    const submitBtn = screen.getByRole('button', { name: /create patient account/i })
    expect(submitBtn).toBeDisabled()
  })

  it('submits registration, receives token, and loads patient dashboard', async () => {
    const patientUser = {
      id: 42,
      email: 'jane@patient.test',
      full_name: 'Jane Patient',
      role: 'patient' as const,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      last_login_at: '2026-01-01T00:00:00Z',
    }

    mockApi({
      authenticated: false,
      register: () => json({ access_token: 'new-patient-token', token_type: 'bearer' }, 201),
      me: () => json(patientUser),
    })

    const user = renderApp()
    await user.click(screen.getByRole('link', { name: /create an account/i }))

    await user.type(screen.getByLabelText(/full name/i), 'Jane Patient')
    await user.type(screen.getByLabelText(/^email address/i), 'jane@patient.test')
    await user.type(screen.getByLabelText(/^password/i), 'SecurePassword123!')
    await user.type(screen.getByLabelText(/^confirm password$/i), 'SecurePassword123!')

    const submitBtn = screen.getByRole('button', { name: /create patient account/i })
    expect(submitBtn).toBeEnabled()
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('PATIENT')).toBeInTheDocument()
      expect(screen.getByText(/welcome, jane patient/i)).toBeInTheDocument()
    })
  })

  it('navigates immediately to login page when logging out after registration', async () => {
    const patientUser = {
      id: 42,
      email: 'jane@patient.test',
      full_name: 'Jane Patient',
      role: 'patient' as const,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      last_login_at: '2026-01-01T00:00:00Z',
    }

    mockApi({
      authenticated: false,
      register: () => json({ access_token: 'new-patient-token', token_type: 'bearer' }, 201),
      me: () => json(patientUser),
    })

    const user = renderApp()
    await user.click(screen.getByRole('link', { name: /create an account/i }))

    await user.type(screen.getByLabelText(/full name/i), 'Jane Patient')
    await user.type(screen.getByLabelText(/^email address/i), 'jane@patient.test')
    await user.type(screen.getByLabelText(/^password/i), 'SecurePassword123!')
    await user.type(screen.getByLabelText(/^confirm password$/i), 'SecurePassword123!')

    await user.click(screen.getByRole('button', { name: /create patient account/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
    })

    // Click Sign Out
    await user.click(screen.getByRole('button', { name: /sign out/i }))

    // Must immediately navigate to sign-in page, NOT register page
    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Sign in to ClariDx', level: 2 }),
      ).toBeInTheDocument()
    })
    expect(
      screen.queryByRole('heading', { name: 'Create Patient Account' }),
    ).not.toBeInTheDocument()
  })

  it('displays error banner if email is already registered', async () => {
    mockApi({
      authenticated: false,
      register: () => json({ detail: 'An account with this email address already exists.' }, 409),
    })

    const user = renderApp()
    await user.click(screen.getByRole('link', { name: /create an account/i }))

    await user.type(screen.getByLabelText(/full name/i), 'Existing User')
    await user.type(screen.getByLabelText(/^email address/i), 'duplicate@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'SecurePassword123!')
    await user.type(screen.getByLabelText(/^confirm password$/i), 'SecurePassword123!')

    await user.click(screen.getByRole('button', { name: /create patient account/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/already exists/i)
    })
  })
})
