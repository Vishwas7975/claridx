import type { components } from './schema'

type Schemas = components['schemas']

export type FeatureSpec = Schemas['FeatureSpecOut']
export type PredictionRequest = Schemas['PredictionRequest']
export type PredictionResponse = Schemas['PredictionResponse']
export type Contribution = Schemas['ContributionOut']
export type Explanation = Schemas['ExplanationOut']
export type Sensitivity = Schemas['SensitivityOut']
export type FeatureImpact = Schemas['FeatureImpactOut']
export type ModelName = NonNullable<PredictionRequest['model_name']>

/** Measurements keyed by feature name; missing measurements are simply absent. */
export type Patient = Record<string, number>

export type DiabetesPatientInput = Schemas['DiabetesPatientInput']
export type DiabetesPredictionRequest = Schemas['DiabetesPredictionRequest']
export type DiabetesPredictionResponse = Schemas['DiabetesPredictionResponse']
export type DiabetesAgreement = Schemas['DiabetesAgreementOut']
export type DiabetesModelName = NonNullable<DiabetesPredictionRequest['model_name']>
export type ModelInfo = Schemas['ModelInfo']
export type ModelsResponse = Schemas['ModelsResponse']

export type TokenResponse = Schemas['TokenResponse']
export type UserProfileResponse = Schemas['UserProfileResponse']
export type UserProfile = UserProfileResponse
export type UserRole = Schemas['UserRole']
export interface LoginRequest {
  email: string
  password: string
}

export type RegisterRequest = Schemas['RegisterRequest']
export type HistoryRecord = Schemas['HistoryRecordOut']
export type HistoryListResponse = Schemas['HistoryListResponse']
export type EnsembleOut = Schemas['EnsembleOut']
export type ModelExecutionOut = Schemas['ModelExecutionOut']
