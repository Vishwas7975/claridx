import { useState } from 'react'
import type { FieldIssue } from '../../api/errors'
import type { FeatureSpec, ModelName, Patient } from '../../api/types'
import { EXAMPLES } from './examples'
import { MIN_MEASUREMENTS, validateForm, type FormValues } from './form'
import { fieldLabel } from './format'

const MODEL_OPTIONS: { value: ModelName; label: string }[] = [
  { value: 'random_forest', label: 'Random Forest (primary model)' },
  { value: 'logistic_regression', label: 'Logistic Regression (interpretable reference)' },
]

interface Props {
  specs: FeatureSpec[]
  values: FormValues
  onChange: (name: string, value: string) => void
  onApplyExample: (patient: Patient) => void
  onClear: () => void
  modelName: ModelName
  onModelChange: (name: ModelName) => void
  serverIssues: FieldIssue[]
  submitting: boolean
  onSubmit: () => void
  canPredict?: boolean
}

function rangeHint(spec: FeatureSpec): string | null {
  if (spec.kind !== 'number' || spec.minimum === null || spec.maximum === null) return null
  return `${spec.minimum}\u2013${spec.maximum}`
}

interface FieldProps {
  spec: FeatureSpec
  value: string
  error: string | null
  onChange: (value: string) => void
  onBlur: () => void
}

function Field({ spec, value, error, onChange, onBlur }: FieldProps) {
  const id = `field-${spec.name}`
  const hint = rangeHint(spec)
  const describedBy =
    [hint !== null ? `${id}-hint` : null, error !== null ? `${id}-error` : null]
      .filter(Boolean)
      .join(' ') || undefined
  const invalid = error !== null ? true : undefined

  return (
    <div className={error !== null ? 'field invalid' : 'field'}>
      <label htmlFor={id}>{fieldLabel(spec)}</label>
      {spec.kind === 'category' ? (
        <select
          id={id}
          value={value}
          aria-invalid={invalid}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
          onBlur={onBlur}
        >
          <option value="">Not provided</option>
          {spec.options.map((option) => (
            <option key={option.value} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          value={value}
          aria-invalid={invalid}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
          onBlur={onBlur}
        />
      )}
      {hint !== null && (
        <p id={`${id}-hint`} className="hint">
          {hint}
        </p>
      )}
      {error !== null && (
        <p id={`${id}-error`} className="error">
          {error}
        </p>
      )}
    </div>
  )
}

export function PatientForm({
  specs,
  values,
  onChange,
  onApplyExample,
  onClear,
  modelName,
  onModelChange,
  serverIssues,
  submitting,
  onSubmit,
  canPredict = true,
}: Props) {
  // A field's own mistakes are shown once the user has left it, not while typing.
  const [touched, setTouched] = useState<ReadonlySet<string>>(new Set())
  const validation = validateForm(specs, values)

  const serverByField = new Map<string, string>()
  const generalIssues: string[] = []
  for (const issue of serverIssues) {
    if (issue.field === null) generalIssues.push(issue.message)
    else serverByField.set(issue.field, issue.message)
  }

  function touch(name: string) {
    setTouched((current) => (current.has(name) ? current : new Set(current).add(name)))
  }

  const invalidCount = Object.keys(validation.errors).length
  let status = `${validation.provided} of ${specs.length} measurements entered.`
  if (invalidCount > 0) {
    status += ` ${invalidCount} ${invalidCount === 1 ? 'value needs' : 'values need'} correcting.`
  } else if (validation.provided < MIN_MEASUREMENTS) {
    status += ` Enter at least ${MIN_MEASUREMENTS} to analyse.`
  }

  return (
    <form
      className="panel"
      noValidate
      onSubmit={(event) => {
        event.preventDefault()
        if (validation.canSubmit && !submitting) onSubmit()
      }}
    >
      <h2>Patient measurements</h2>
      <p className="hint">
        Leave a field blank if the measurement is not available. At least {MIN_MEASUREMENTS} of{' '}
        {specs.length} are needed.
      </p>

      <div className="examples" role="group" aria-label="Examples">
        {EXAMPLES.map((example) => (
          <button
            key={example.id}
            type="button"
            className="secondary"
            onClick={() => onApplyExample(example.values)}
          >
            {example.label}
          </button>
        ))}
      </div>

      <div className="fields">
        {specs.map((spec) => (
          <Field
            key={spec.name}
            spec={spec}
            value={values[spec.name] ?? ''}
            error={
              (touched.has(spec.name) ? validation.errors[spec.name] : undefined) ??
              serverByField.get(spec.name) ??
              null
            }
            onChange={(value) => onChange(spec.name, value)}
            onBlur={() => touch(spec.name)}
          />
        ))}
      </div>

      <div className="field model">
        <label htmlFor="model">Model</label>
        <select
          id="model"
          value={modelName}
          onChange={(event) => onModelChange(event.target.value as ModelName)}
        >
          {MODEL_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <p role="status" className="status">
        {status}
      </p>
      {generalIssues.map((message) => (
        <p key={message} role="alert" className="error">
          {message}
        </p>
      ))}

      <div className="actions">
        {canPredict ? (
          <button type="submit" disabled={!validation.canSubmit || submitting}>
            {submitting ? 'Analysing\u2026' : 'Analyse'}
          </button>
        ) : (
          <p className="role-restriction-note" role="note">
            Prediction generation is restricted to Doctor and Admin accounts.
          </p>
        )}
        <button
          type="button"
          className="secondary"
          onClick={() => {
            setTouched(new Set())
            onClear()
          }}
        >
          Clear
        </button>
      </div>
    </form>
  )
}
