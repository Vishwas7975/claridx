import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

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
})
