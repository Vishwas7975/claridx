import type { FeatureSpec } from '../api/types'
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
