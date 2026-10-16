import type { FeatureSpec, Sensitivity } from '../api/types'
import diabetesFeaturesJson from './fixtures/diabetes-features.json?raw'
import featuresJson from './fixtures/heart-features.json?raw'

// Generated from the backend by `npm run api:sync`; do not edit the JSON by hand.
export const heartFixture = JSON.parse(featuresJson) as {
  min_measurements: number
  features: FeatureSpec[]
}

export const diabetesFixture = JSON.parse(diabetesFeaturesJson) as {
  min_measurements: number
  features: FeatureSpec[]
}

export const diabetesModelsFixture = {
  model_version: 'test-1',
  primary: 'logistic_regression',
  models: [
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
  ],
}

export const diabetesSensitivityFixture: Sensitivity = {
  baseline_probability: 0.35,
  probability_min: 0.22,
  probability_max: 0.68,
  typical_low: 0.28,
  typical_high: 0.58,
  positive_share: 0.42,
  verdict_uncertain: true,
  patterns_used: 120,
  impacts: [
    {
      feature: 'insu',
      label: '2-Hour serum insulin',
      can_flip: false,
      probability_min: 0.27,
      probability_max: 0.5,
      typical_low: 0.3,
      typical_high: 0.45,
    },
    {
      feature: 'skin',
      label: 'Triceps skin fold thickness',
      can_flip: false,
      probability_min: 0.31,
      probability_max: 0.41,
      typical_low: 0.32,
      typical_high: 0.39,
    },
  ],
  note: 'Simulated across 120 background cases with observed patterns.',
}
