import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { FieldIssue } from '../../api/errors'
import type { DiabetesModelName, ModelInfo } from '../../api/types'
import { diabetesFixture, diabetesModelsFixture } from '../../test/fixtures'
import { EXAMPLES } from './examples'
import { toFormValues, type FormValues } from './form'
import { fieldLabel } from './format'
import { PatientForm } from './PatientForm'

function Harness({
  onSubmit = () => {},
  serverIssues = [],
  models = diabetesModelsFixture.models as ModelInfo[],
}: {
  onSubmit?: () => void
  serverIssues?: FieldIssue[]
  models?: ModelInfo[]
}) {
  const [values, setValues] = useState<FormValues>({})
  const [modelName, setModelName] = useState<DiabetesModelName>('logistic_regression')
  return (
    <PatientForm
      specs={diabetesFixture.features}
      models={models}
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

const high = EXAMPLES[0] // 8 of 8
const minimal = EXAMPLES[2] // 5 of 8, preg=0

describe('PatientForm', () => {
  it('shows one labelled control per feature', () => {
    render(<Harness />)
    for (const spec of diabetesFixture.features) {
      expect(screen.getByLabelText(fieldLabel(spec))).toBeInTheDocument()
    }
  })

  it('explains what is still needed and keeps submit disabled', () => {
    render(<Harness />)
    expect(screen.getByRole('status')).toHaveTextContent(
      '0 of 8 measurements entered. Enter at least 5 to analyse.',
    )
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('counts measurements as they are entered and enables submit at the minimum', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: minimal.label }))
    expect(screen.getByRole('status')).toHaveTextContent('5 of 8 measurements entered.')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeEnabled()
  })

  it('counts preg = 0 as an effective measurement', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    // Enter 5 measurements where preg is 0
    await user.type(screen.getByLabelText('Number of pregnancies'), '0')
    await user.type(screen.getByLabelText('Plasma glucose concentration (mg/dL)'), '120')
    await user.type(screen.getByLabelText('Diastolic blood pressure (mm Hg)'), '80')
    await user.type(screen.getByLabelText('Body mass index (kg/m^2)'), '25.5')
    await user.type(screen.getByLabelText('Age (years)'), '30')

    expect(screen.getByRole('status')).toHaveTextContent('5 of 8 measurements entered.')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeEnabled()
  })

  it('does not count suspicious zeros in plas, pres, skin, insu, mass as effective measurements', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    // Enter 4 valid measurements plus 1 suspicious zero
    await user.type(screen.getByLabelText('Number of pregnancies'), '1')
    await user.type(screen.getByLabelText('Plasma glucose concentration (mg/dL)'), '120')
    await user.type(screen.getByLabelText('Diastolic blood pressure (mm Hg)'), '80')
    await user.type(screen.getByLabelText('Age (years)'), '30')
    // insu = 0 does not count
    await user.type(screen.getByLabelText('2-Hour serum insulin (mu U/ml)'), '0')

    // Only 4 effective measurements
    expect(screen.getByRole('status')).toHaveTextContent(
      '4 of 8 measurements entered. Enter at least 5 to analyse.',
    )
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('marks a field invalid only after the user has left it', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const age = screen.getByLabelText('Age (years)')

    await user.type(age, '19')
    expect(screen.queryByText('Must be at least 21')).not.toBeInTheDocument()

    await user.tab()
    expect(await screen.findByText('Must be at least 21')).toBeInTheDocument()
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
    await user.type(age, '15')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('fills the form from an example and empties it again with Clear', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: high.label }))
    expect(screen.getByLabelText('Number of pregnancies')).toHaveValue('6')
    expect(screen.getByLabelText('Plasma glucose concentration (mg/dL)')).toHaveValue('168')
    expect(screen.getByLabelText('Age (years)')).toHaveValue('48')
    expect(screen.getByRole('status')).toHaveTextContent('8 of 8 measurements entered')

    await user.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.getByLabelText('Number of pregnancies')).toHaveValue('')
    expect(screen.getByRole('status')).toHaveTextContent('0 of 8 measurements entered')
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
    await user.type(screen.getByLabelText('Age (years)'), '30{Enter}')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('defaults model selector to logistic_regression and offers only models from API', () => {
    render(<Harness />)
    const select = screen.getByLabelText('Model') as HTMLSelectElement
    expect(select.value).toBe('logistic_regression')
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(2)
    expect(options[0]).toHaveTextContent(
      'Logistic Regression (calibrated, interpretable reference)',
    )
    expect(options[1]).toHaveTextContent('Random Forest (tree ensemble)')
  })

  it('shows issues reported by the server next to the field or as a general message', () => {
    render(
      <Harness
        serverIssues={[
          { field: 'age', message: 'Server rejected this age value' },
          { field: null, message: 'General server problem' },
        ]}
      />,
    )
    expect(screen.getByText('Server rejected this age value')).toBeInTheDocument()
    expect(screen.getByText('General server problem')).toBeInTheDocument()
  })
})
