import type { Patient } from '../../api/types'

export interface Example {
  id: string
  label: string
  values: Patient
}

const HIGH_RISK: Patient = {
  age: 59,
  sex: 1,
  cp: 4,
  trestbps: 140,
  chol: 240,
  fbs: 0,
  restecg: 2,
  thalach: 120,
  exang: 1,
  oldpeak: 2,
  slope: 2,
  ca: 2,
  thal: 7,
}

const LOW_RISK: Patient = {
  age: 45,
  sex: 0,
  cp: 2,
  trestbps: 120,
  chol: 200,
  fbs: 0,
  restecg: 0,
  thalach: 170,
  exang: 0,
  oldpeak: 0,
  slope: 1,
  ca: 0,
  thal: 3,
}

const MISSING_IN_INCOMPLETE = ['chol', 'ca', 'thal']
const INCOMPLETE: Patient = Object.fromEntries(
  Object.entries(HIGH_RISK).filter(([name]) => !MISSING_IN_INCOMPLETE.includes(name)),
)

// Omitting thal, ca, cp and slope (4 of the most influential features) places the
// positive-share near 67%, within the 10–90% uncertainty band (decision #23).
// Verified as the first candidate listed in the handoff; the exact probability
// and share depend on the trained model artifact.
const MISSING_IN_UNCERTAIN = ['thal', 'ca', 'cp', 'slope']
const UNCERTAIN: Patient = Object.fromEntries(
  Object.entries(HIGH_RISK).filter(([name]) => !MISSING_IN_UNCERTAIN.includes(name)),
)

/** Illustrative values for trying the tool out; they are not real patients. */
export const EXAMPLES: Example[] = [
  { id: 'high', label: 'Example: high-risk pattern', values: HIGH_RISK },
  { id: 'low', label: 'Example: low-risk pattern', values: LOW_RISK },
  { id: 'incomplete', label: 'Example: 3 measurements missing', values: INCOMPLETE },
  { id: 'uncertain', label: 'Example: uncertain verdict (4 missing)', values: UNCERTAIN },
]
