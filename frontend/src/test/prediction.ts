import type { PredictionResponse } from '../api/types'

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
