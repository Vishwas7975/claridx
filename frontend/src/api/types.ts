import type { components } from './schema'

type Schemas = components['schemas']

export type FeatureSpec = Schemas['FeatureSpecOut']
export type PredictionRequest = Schemas['PredictionRequest']
export type PredictionResponse = Schemas['PredictionResponse']
export type Contribution = Schemas['ContributionOut']
export type Explanation = Schemas['ExplanationOut']
export type Sensitivity = Schemas['SensitivityOut']
export type ModelName = NonNullable<PredictionRequest['model_name']>

/** Measurements keyed by feature name; missing measurements are simply absent. */
export type Patient = Record<string, number>
