import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { toApiError } from '../../api/errors'
import type {
  FeatureSpec,
  ModelName,
  Patient,
  PredictionRequest,
  PredictionResponse,
} from '../../api/types'

export interface PredictionInput {
  patient: Patient
  modelName: ModelName
}

/**
 * The form validates every value against the API's own feature specs (see form.ts and its
 * tests), so the numbers are known to fit the stricter generated types, for example the
 * 0 | 1 codes. TypeScript cannot see that, so the conversion is made here, once.
 */
function toPatientInput(patient: Patient): PredictionRequest['patient'] {
  return patient as unknown as PredictionRequest['patient']
}

export function useFeatures() {
  return useQuery<FeatureSpec[], Error>({
    queryKey: ['heart', 'features'],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/heart/features')
      if (data === undefined) throw toApiError(error, response.status)
      return data
    },
  })
}

export function usePrediction() {
  return useMutation<PredictionResponse, Error, PredictionInput>({
    mutationFn: async ({ patient, modelName }) => {
      const { data, error, response } = await api.POST('/api/v1/heart/predictions', {
        body: { model_name: modelName, patient: toPatientInput(patient) },
      })
      if (data === undefined) throw toApiError(error, response.status)
      return data
    },
  })
}
