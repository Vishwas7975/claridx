import type { FeatureSpec } from '../api/types'
import featuresJson from './fixtures/heart-features.json?raw'

// Generated from the backend by `npm run api:sync`; do not edit the JSON by hand.
export const heartFixture = JSON.parse(featuresJson) as {
  min_measurements: number
  features: FeatureSpec[]
}
