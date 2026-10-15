import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { toApiError } from '../../api/errors'
import type {
  DiabetesModelName,
  DiabetesPatientInput,
  DiabetesPredictionResponse,
  FeatureSpec,
  ModelInfo,
  ModelsResponse,
} from '../../api/types'

export interface DiabetesPredictionInput {
  patient: DiabetesPatientInput
  modelName: DiabetesModelName
}

export function useFeatures() {
  return useQuery<FeatureSpec[], Error>({
    queryKey: ['diabetes', 'features'],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/diabetes/features')
      if (data === undefined) throw toApiError(error, response.status)
      return data
    },
  })
}

export function useModels() {
  return useQuery<ModelsResponse, Error>({
    queryKey: ['diabetes', 'models'],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/diabetes/models')
      if (data === undefined) throw toApiError(error, response.status)
      return data
    },
  })
}

export function usePrediction() {
  return useMutation<DiabetesPredictionResponse, Error, DiabetesPredictionInput>({
    mutationFn: async ({ patient, modelName }) => {
      const { data, error, response } = await api.POST('/api/v1/diabetes/predictions', {
        body: { model_name: modelName, patient },
      })
      if (data === undefined) throw toApiError(error, response.status)
      return data
    },
  })
}

export { useFeatures as useDiabetesFeatures }
export { useModels as useDiabetesModels }
export { usePrediction as useDiabetesPrediction }
export type { ModelInfo, ModelsResponse }
