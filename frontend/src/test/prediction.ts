import type { DiabetesPredictionResponse, PredictionResponse, Sensitivity } from '../api/types'
import { diabetesSensitivityFixture } from './fixtures'

/** A realistic sensitivity result for tests; override any part. */
export function makeSensitivity(overrides: Partial<Sensitivity> = {}): Sensitivity {
  return {
    baseline_probability: 0.615,
    probability_min: 0.58,
    probability_max: 0.996,
    typical_low: 0.59,
    typical_high: 0.996,
    positive_share: 1,
    verdict_uncertain: false,
    patterns_used: 240,
    impacts: [],
    note: 'Simulated from background patient profiles.',
    ...overrides,
  }
}

/** A realistic diabetes sensitivity result for tests; override any part. */
export function makeDiabetesSensitivity(overrides: Partial<Sensitivity> = {}): Sensitivity {
  return {
    ...diabetesSensitivityFixture,
    ...overrides,
  }
}

/** A realistic prediction response for tests; override any part. */
export function makePrediction(overrides: Partial<PredictionResponse> = {}): PredictionResponse {
  return {
    model_name: 'random_forest',
    model_version: 'heart-test',
    probability: 0.615,
    threshold: 0.5,
    predicted_positive: true,
    calibrated: false,
    imputed_features: [],
    warnings: [],
    shap: {
      method: 'shap',
      output_space: 'probability',
      base_value: 0.463,
      fidelity: null,
      low_confidence: false,
      contributions: [
        {
          feature: 'thal',
          label: 'Thallium stress test result',
          value: 7,
          imputed: false,
          contribution: 0.146,
        },
        { feature: 'cp', label: 'Chest pain type', value: 4, imputed: false, contribution: 0.082 },
        {
          feature: 'ca',
          label: 'Major vessels coloured by fluoroscopy',
          value: null,
          imputed: true,
          contribution: -0.079,
        },
      ],
    },
    lime: {
      method: 'lime',
      output_space: 'probability',
      base_value: null,
      fidelity: 0.75,
      low_confidence: false,
      contributions: [
        {
          feature: 'thal',
          label: 'Thallium stress test result',
          value: 7,
          imputed: false,
          contribution: 0.26,
        },
        { feature: 'cp', label: 'Chest pain type', value: 4, imputed: false, contribution: 0.157 },
        {
          feature: 'ca',
          label: 'Major vessels coloured by fluoroscopy',
          value: null,
          imputed: true,
          contribution: -0.154,
        },
      ],
    },
    agreement: { rank_correlation: 0.9, top_k_overlap: 1, sign_agreement: 1, k: 3 },
    sensitivity: null,
    disclaimer: 'Decision support only, not a diagnosis.',
    ...overrides,
  }
}

/** A realistic diabetes prediction response for tests; override any part. */
export function makeDiabetesPrediction(
  overrides: Partial<DiabetesPredictionResponse> = {},
): DiabetesPredictionResponse {
  return {
    model_name: 'logistic_regression',
    model_version: 'diabetes-test',
    probability: 0.35,
    threshold: 0.34,
    predicted_positive: true,
    calibrated: true,
    imputed_features: [],
    warnings: [],
    shap: {
      method: 'shap',
      output_space: 'log_odds',
      base_value: -0.84,
      fidelity: null,
      low_confidence: false,
      contributions: [
        {
          feature: 'plas',
          label: 'Plasma glucose concentration',
          value: 148,
          imputed: false,
          contribution: 0.62,
        },
        {
          feature: 'mass',
          label: 'Body mass index',
          value: 33.6,
          imputed: false,
          contribution: 0.38,
        },
        {
          feature: 'age',
          label: 'Age',
          value: 50,
          imputed: false,
          contribution: 0.21,
        },
      ],
    },
    lime: {
      method: 'lime',
      output_space: 'probability',
      base_value: null,
      fidelity: 0.82,
      low_confidence: false,
      contributions: [
        {
          feature: 'plas',
          label: 'Plasma glucose concentration',
          value: 148,
          imputed: false,
          contribution: 0.18,
        },
        {
          feature: 'mass',
          label: 'Body mass index',
          value: 33.6,
          imputed: false,
          contribution: 0.11,
        },
        {
          feature: 'age',
          label: 'Age',
          value: 50,
          imputed: false,
          contribution: 0.07,
        },
      ],
    },
    agreement: null,
    sensitivity: null,
    disclaimer:
      'Research prototype for decision support and education only. It is not a medical device and must not be used for diagnosis or treatment.',
    ...overrides,
  }
}

/** A realistic diabetes prediction response with computed sensitivity for tests. */
export function makeDiabetesPredictionWithSensitivity(
  overrides: Partial<DiabetesPredictionResponse> = {},
  sensitivityOverrides: Partial<Sensitivity> = {},
): DiabetesPredictionResponse {
  return makeDiabetesPrediction({
    imputed_features: ['insu', 'skin'],
    sensitivity: makeDiabetesSensitivity(sensitivityOverrides),
    ...overrides,
  })
}
