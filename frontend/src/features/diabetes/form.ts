import type { DiabetesPatientInput, FeatureSpec } from '../../api/types'

/** Mirrors the backend's MIN_EFFECTIVE_FEATURES; a test compares it with the generated fixture. */
export const MIN_MEASUREMENTS = 5

/** Features where zero values indicate unmeasured data in the Pima dataset and backend. */
export const SUSPICIOUS_ZERO_FEATURES: ReadonlySet<string> = new Set([
  'plas',
  'pres',
  'skin',
  'insu',
  'mass',
])

/** Raw text of every input, keyed by feature name. */
export type FormValues = Record<string, string>

export interface Validation {
  errors: Record<string, string>
  provided: number
  canSubmit: boolean
}

/** Returns true if a valid measurement counts toward the minimum required input. */
export function isEffectiveMeasurement(feature: string, value: number): boolean {
  if (SUSPICIOUS_ZERO_FEATURES.has(feature) && value === 0) {
    return false
  }
  return true
}

/** Returns a message when a non-blank entry is not acceptable for this feature. */
export function fieldError(spec: FeatureSpec, raw: string): string | null {
  const text = raw.trim()
  if (text === '') return null

  const value = Number(text)
  if (!Number.isFinite(value)) return 'Enter a number'

  if (spec.step !== null && spec.step >= 1 && !Number.isInteger(value)) {
    return 'Enter a whole number'
  }
  if (spec.minimum !== null && value < spec.minimum) {
    return `Must be at least ${spec.minimum}`
  }
  if (spec.maximum !== null && value > spec.maximum) {
    return `Must be at most ${spec.maximum}`
  }
  return null
}

/** The measurements to send: blank and invalid entries are left out. */
export function buildPatient(specs: FeatureSpec[], values: FormValues): DiabetesPatientInput {
  const patient: Record<string, number> = {}
  for (const spec of specs) {
    const raw = (values[spec.name] ?? '').trim()
    if (raw === '' || fieldError(spec, raw) !== null) continue
    patient[spec.name] = Number(raw)
  }
  return patient as unknown as DiabetesPatientInput
}

/** Count valid measurements that are not suspicious zeros. */
export function countEffectiveMeasurements(patient: DiabetesPatientInput): number {
  let count = 0
  for (const [feature, value] of Object.entries(patient)) {
    if (value !== null && value !== undefined && isEffectiveMeasurement(feature, value)) {
      count += 1
    }
  }
  return count
}

export function validateForm(specs: FeatureSpec[], values: FormValues): Validation {
  const errors: Record<string, string> = {}
  for (const spec of specs) {
    const message = fieldError(spec, values[spec.name] ?? '')
    if (message !== null) errors[spec.name] = message
  }
  const patient = buildPatient(specs, values)
  const provided = countEffectiveMeasurements(patient)
  return {
    errors,
    provided,
    canSubmit: Object.keys(errors).length === 0 && provided >= MIN_MEASUREMENTS,
  }
}

export function toFormValues(patient: DiabetesPatientInput): FormValues {
  return Object.fromEntries(
    Object.entries(patient)
      .filter(([, value]) => value !== null && value !== undefined)
      .map(([name, value]) => [name, String(value)]),
  )
}
