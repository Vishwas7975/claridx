import { useState } from 'react'
import type { FieldIssue } from '../../api/errors'
import type {
  DiabetesModelName,
  DiabetesPatientInput,
  FeatureSpec,
  ModelInfo,
} from '../../api/types'
import { EXAMPLES } from './examples'
import { MIN_MEASUREMENTS, validateForm, type FormValues } from './form'
import { fieldLabel } from './format'

const DEFAULT_MODELS: ModelInfo[] = [
  {
    name: 'logistic_regression',
    role: 'primary',
    description: 'Logistic Regression (calibrated, interpretable reference)',
  },
  {
    name: 'random_forest',
    role: 'glass_box_reference',
    description: 'Random Forest (tree ensemble)',
  },
]

interface Props {
  specs: FeatureSpec[]
  models?: ModelInfo[]
  values: FormValues
  onChange: (name: string, value: string) => void
  onApplyExample: (patient: DiabetesPatientInput) => void
  onClear: () => void
  modelName: DiabetesModelName
  onModelChange: (name: DiabetesModelName) => void
  serverIssues: FieldIssue[]
  submitting: boolean
  onSubmit: () => void
  canPredict?: boolean
  hideModelSelector?: boolean
}

function rangeHint(spec: FeatureSpec): string | null {
  if (spec.kind !== 'number' || spec.minimum === null || spec.maximum === null) return null
  return `${spec.minimum}–${spec.maximum}`
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
          {spec.name === 'preg'
            ? `${hint} • Research cohort feature (Pima Indians study; females aged 21+). 0 is valid if non-applicable or never pregnant. Note: Model validity outside this historical female cohort is uncertain.`
            : hint}
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

interface FieldGroup {
  id: string
  title: string
  fieldNames: string[]
}

const DIABETES_FIELD_GROUPS: FieldGroup[] = [
  {
    id: 'profile',
    title: 'Patient Profile',
    fieldNames: ['age', 'preg', 'mass', 'pedi'],
  },
  {
    id: 'metabolic',
    title: 'Metabolic & Diagnostic Measurements',
    fieldNames: ['plas', 'insu', 'pres', 'skin'],
  },
]

function groupSpecs(specs: FeatureSpec[], groups: FieldGroup[]) {
  const specMap = new Map(specs.map((s) => [s.name, s]))
  const assigned = new Set<string>()
  const result: { group: FieldGroup; specs: FeatureSpec[] }[] = []

  for (const group of groups) {
    const matched: FeatureSpec[] = []
    for (const name of group.fieldNames) {
      const spec = specMap.get(name)
      if (spec) {
        matched.push(spec)
        assigned.add(name)
      }
    }
    if (matched.length > 0) {
      result.push({ group, specs: matched })
    }
  }

  const remaining = specs.filter((s) => !assigned.has(s.name))
  if (remaining.length > 0) {
    result.push({
      group: { id: 'other', title: 'Other Measurements', fieldNames: [] },
      specs: remaining,
    })
  }

  return result
}

function modelShortLabel(name: string): string {
  if (name === 'logistic_regression') return 'Logistic Regression'
  if (name === 'random_forest') return 'Random Forest'
  return name
}

export function PatientForm({
  specs,
  models,
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
  hideModelSelector = false,
}: Props) {
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

  const modelOptions = models && models.length > 0 ? models : DEFAULT_MODELS
  const grouped = groupSpecs(specs, DIABETES_FIELD_GROUPS)

  return (
    <form
      className="panel"
      noValidate
      onSubmit={(event) => {
        event.preventDefault()
        if (validation.canSubmit && !submitting) onSubmit()
      }}
    >
      <div className="panel-header-compact">
        <h2>Patient measurements</h2>
        <p className="hint">
          Leave blank if unavailable. At least {MIN_MEASUREMENTS} of {specs.length} are required.
        </p>
      </div>

      <div className="examples-section">
        <span className="examples-label">Load Reference Patient:</span>
        <div className="examples-grid" role="group" aria-label="Examples">
          {EXAMPLES.map((example) => (
            <button
              key={example.id}
              type="button"
              className="secondary sm example-btn"
              onClick={() => onApplyExample(example.values)}
            >
              {example.label}
            </button>
          ))}
        </div>
      </div>

      <div className="form-sections">
        {grouped.map(({ group, specs: sectionSpecs }) => (
          <div key={group.id} className="form-section">
            <h3 className="form-section-title">{group.title}</h3>
            <div className="fields">
              {sectionSpecs.map((spec) => (
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
          </div>
        ))}
      </div>

      {!hideModelSelector && (
        <div className="field model">
          <label htmlFor="model">Model</label>
          <select
            id="model"
            value={modelName}
            aria-describedby="diabetes-model-desc"
            onChange={(event) => onModelChange(event.target.value as DiabetesModelName)}
          >
            {modelOptions.map((option) => (
              <option key={option.name} value={option.name} label={modelShortLabel(option.name)}>
                {option.description || option.name}
              </option>
            ))}
          </select>
          {modelOptions.find((option) => option.name === modelName)?.description && (
            <p id="diabetes-model-desc" className="hint model-desc">
              {modelOptions.find((option) => option.name === modelName)?.description}
            </p>
          )}
        </div>
      )}

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
            {submitting ? 'Analysing…' : 'Analyse'}
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
