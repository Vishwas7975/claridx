import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { FieldIssue } from '../../api/errors'
import type { ModelName } from '../../api/types'
import { heartFixture } from '../../test/fixtures'
import { EXAMPLES } from './examples'
import { toFormValues, type FormValues } from './form'
import { fieldLabel } from './format'
import { PatientForm } from './PatientForm'

function Harness({
  onSubmit = () => {},
  serverIssues = [],
}: {
  onSubmit?: () => void
  serverIssues?: FieldIssue[]
}) {
  const [values, setValues] = useState<FormValues>({})
  const [modelName, setModelName] = useState<ModelName>('random_forest')
  return (
    <PatientForm
      specs={heartFixture.features}
      values={values}
      onChange={(name, value) => setValues((current) => ({ ...current, [name]: value }))}
      onApplyExample={(patient) => setValues(toFormValues(patient))}
      onClear={() => setValues({})}
      modelName={modelName}
      onModelChange={setModelName}
      serverIssues={serverIssues}
      submitting={false}
      onSubmit={onSubmit}
    />
  )
}

const high = EXAMPLES[0]
const incomplete = EXAMPLES[2]

describe('PatientForm', () => {
  it('shows one labelled control per feature', () => {
    render(<Harness />)
    for (const spec of heartFixture.features) {
      expect(screen.getByLabelText(fieldLabel(spec))).toBeInTheDocument()
    }
  })

  it('explains what is still needed and keeps submit disabled', () => {
    render(<Harness />)
    expect(screen.getByRole('status')).toHaveTextContent(
      '0 of 13 measurements entered. Enter at least 7 to analyse.',
    )
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('counts measurements as they are entered and enables submit at the minimum', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: incomplete.label }))
    expect(screen.getByRole('status')).toHaveTextContent('10 of 13 measurements entered.')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeEnabled()
  })

  it('marks a field invalid only after the user has left it', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const age = screen.getByLabelText('Age (years)')

    await user.type(age, '130')
    expect(screen.queryByText('Must be at most 120')).not.toBeInTheDocument()

    await user.tab()
    expect(await screen.findByText('Must be at most 120')).toBeInTheDocument()
    expect(age).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('status')).toHaveTextContent('1 value needs correcting')
  })

  it('keeps submit disabled while any value is invalid', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: high.label }))
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeEnabled()

    const age = screen.getByLabelText('Age (years)')
    await user.clear(age)
    await user.type(age, '130')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('fills the form from an example and empties it again with Clear', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: high.label }))
    expect(screen.getByLabelText('Age (years)')).toHaveValue('59')
    expect(screen.getByLabelText('Sex')).toHaveValue('1')
    expect(screen.getByLabelText('Thallium stress test result')).toHaveValue('7')
    expect(screen.getByRole('status')).toHaveTextContent('13 of 13 measurements entered')

    await user.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.getByLabelText('Age (years)')).toHaveValue('')
    expect(screen.getByRole('status')).toHaveTextContent('0 of 13 measurements entered')
  })

  it('submits through the button and through the Enter key', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<Harness onSubmit={onSubmit} />)
    await user.click(screen.getByRole('button', { name: high.label }))

    await user.click(screen.getByRole('button', { name: 'Analyse' }))
    expect(onSubmit).toHaveBeenCalledTimes(1)

    await user.click(screen.getByLabelText('Age (years)'))
    await user.keyboard('{Enter}')
    expect(onSubmit).toHaveBeenCalledTimes(2)
  })

  it('does not submit when the form is not valid', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<Harness onSubmit={onSubmit} />)
    await user.type(screen.getByLabelText('Age (years)'), '54{Enter}')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows issues reported by the server next to the field or as a general message', () => {
    render(
      <Harness
        serverIssues={[
          { field: 'chol', message: 'Server rejected this cholesterol value' },
          { field: null, message: 'General server problem' },
        ]}
      />,
    )
    expect(screen.getByText('Server rejected this cholesterol value')).toBeInTheDocument()
    expect(screen.getByText('General server problem')).toBeInTheDocument()
  })
})
