import type { DiabetesPatientInput } from '../../api/types'

export interface DiabetesExample {
  id: string
  label: string
  values: DiabetesPatientInput
}

const HIGH_RISK: DiabetesPatientInput = {
  preg: 6,
  plas: 168,
  pres: 82,
  skin: 35,
  insu: 200,
  mass: 38.2,
  pedi: 0.85,
  age: 48,
}

const LOW_RISK: DiabetesPatientInput = {
  preg: 1,
  plas: 92,
  pres: 68,
  skin: 18,
  insu: 65,
  mass: 22.4,
  pedi: 0.23,
  age: 24,
}

const MINIMAL_VALID: DiabetesPatientInput = {
  preg: 0,
  plas: 135,
  pres: 76,
  mass: 29.1,
  age: 36,
}

const ROUTINE_CARE: DiabetesPatientInput = {
  preg: 3,
  plas: 145,
  pres: 78,
  mass: 31.0,
  pedi: 0.52,
  age: 42,
}

export const EXAMPLES: DiabetesExample[] = [
  { id: 'high', label: 'Example: high-risk pattern', values: HIGH_RISK },
  { id: 'low', label: 'Example: low-risk pattern', values: LOW_RISK },
  { id: 'minimal', label: 'Example: minimal (5 measurements, 0 preg)', values: MINIMAL_VALID },
  {
    id: 'routine',
    label: 'Example: routine clinic (skin & insulin missing)',
    values: ROUTINE_CARE,
  },
]
