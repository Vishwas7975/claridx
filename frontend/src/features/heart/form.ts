import type { FeatureSpec, Patient } from '../../api/types'

/** Mirrors the backend's MIN_PROVIDED_FEATURES; a test compares it with the generated fixture. */
export const MIN_MEASUREMENTS = 7

/** Raw text of every input, keyed by feature name. */
export type FormValues = Record<string, string>

export interface Validation {
  errors: Record<string, string>
  provided: number
  canSubmit: boolean
}

/** Returns a message when a non-blank entry is not acceptable for this feature. */
export function fieldError(spec: FeatureSpec, raw: string): string | null {
  const text = raw.trim()
  if (text === '') return null

  const value = Number(text)
  if (!Number.isFinite(value)) return 'Enter a number'

  if (spec.kind === 'category') {
    return spec.options.some((option) => option.value === value)
      ? null
      : 'Choose one of the listed options'
  }
  if (spec.step !== null && spec.step >= 1 && !Number.isInteger(value))
    return 'Enter a whole number'
  if (spec.minimum !== null && value < spec.minimum) return `Must be at least ${spec.minimum}`
  if (spec.maximum !== null && value > spec.maximum) return `Must be at most ${spec.maximum}`
  return null
}

/** The measurements to send: blank and invalid entries are left out. */
export function buildPatient(specs: FeatureSpec[], values: FormValues): Patient {
  const patient: Patient = {}
  for (const spec of specs) {
    const raw = (values[spec.name] ?? '').trim()
    if (raw === '' || fieldError(spec, raw) !== null) continue
    patient[spec.name] = Number(raw)
  }
  return patient
}

export function validateForm(specs: FeatureSpec[], values: FormValues): Validation {
  const errors: Record<string, string> = {}
  for (const spec of specs) {
    const message = fieldError(spec, values[spec.name] ?? '')
    if (message !== null) errors[spec.name] = message
  }
  const provided = Object.keys(buildPatient(specs, values)).length
  return {
    errors,
    provided,
    canSubmit: Object.keys(errors).length === 0 && provided >= MIN_MEASUREMENTS,
  }
}

export function toFormValues(patient: Patient): FormValues {
  return Object.fromEntries(Object.entries(patient).map(([name, value]) => [name, String(value)]))
}
