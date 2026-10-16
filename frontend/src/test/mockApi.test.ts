import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { diabetesFixture, heartFixture } from './fixtures'
import { json, mockApi } from './mockApi'
import {
  makeDiabetesPrediction,
  makeDiabetesPredictionWithSensitivity,
  makePrediction,
} from './prediction'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('mockApi', () => {
  it('serves default heart features and handles heart predictions', async () => {
    const recorded = mockApi({
      predictions: () => json(makePrediction({ probability: 0.72 })),
    })

    const { data: features } = await api.GET('/api/v1/heart/features')
    expect(features).toEqual(heartFixture.features)
    expect(features).toHaveLength(13)

    const payload = {
      model_name: 'random_forest' as const,
      patient: { age: 60, trestbps: 130 },
    }
    const { data: prediction } = await api.POST('/api/v1/heart/predictions', {
      body: payload,
    })
    expect(prediction?.probability).toBe(0.72)
    expect(recorded).toHaveLength(1)
    expect(recorded[0].path).toBe('/api/v1/heart/predictions')
    expect(recorded[0].body).toEqual(payload)
  })

  it('serves default diabetes features and models', async () => {
    mockApi()

    const { data: features } = await api.GET('/api/v1/diabetes/features')
    expect(features).toEqual(diabetesFixture.features)
    expect(features).toHaveLength(8)
    expect(diabetesFixture.min_measurements).toBe(5)

    const { data: models } = await api.GET('/api/v1/diabetes/models')
    expect(models?.primary).toBe('logistic_regression')
    expect(models?.models).toHaveLength(2)
  })

  it('records diabetes prediction calls and returns diabetes prediction response', async () => {
    const expected = makeDiabetesPrediction({ probability: 0.45 })
    const recorded = mockApi({
      diabetesPredictions: () => json(expected),
    })

    const payload = {
      model_name: 'logistic_regression' as const,
      patient: { preg: 1, plas: 120, pres: 70, mass: 28.5, age: 35 },
    }
    const { data: prediction } = await api.POST('/api/v1/diabetes/predictions', {
      body: payload,
    })

    expect(prediction).toEqual(expected)
    expect(prediction?.agreement).toBeNull()
    expect('sensitivity' in (prediction ?? {})).toBe(true)
    expect(prediction?.sensitivity).toBeNull()
    expect(recorded).toHaveLength(1)
    expect(recorded[0].path).toBe('/api/v1/diabetes/predictions')
    expect(recorded[0].body).toEqual(payload)
  })

  it('records diabetes prediction calls and returns response with computed sensitivity', async () => {
    const expected = makeDiabetesPredictionWithSensitivity({ probability: 0.45 })
    const recorded = mockApi({
      diabetesPredictions: () => json(expected),
    })

    const payload = {
      model_name: 'logistic_regression' as const,
      patient: { preg: 1, plas: 120, pres: 70, mass: 28.5, age: 35 },
    }
    const { data: prediction } = await api.POST('/api/v1/diabetes/predictions', {
      body: payload,
    })

    expect(prediction).toEqual(expected)
    expect(prediction?.sensitivity).not.toBeNull()
    expect(prediction?.sensitivity?.verdict_uncertain).toBe(true)
    expect(prediction?.sensitivity?.typical_low).toBe(0.28)
    expect(prediction?.sensitivity?.typical_high).toBe(0.58)
    expect(prediction?.sensitivity?.positive_share).toBe(0.42)
    expect(prediction?.sensitivity?.patterns_used).toBe(120)
    expect(prediction?.sensitivity?.impacts).toHaveLength(2)
    expect(prediction?.sensitivity?.impacts[0].feature).toBe('insu')
    expect(prediction?.imputed_features).toEqual(['insu', 'skin'])
    expect(recorded).toHaveLength(1)
    expect(recorded[0].path).toBe('/api/v1/diabetes/predictions')
    expect(recorded[0].body).toEqual(payload)
  })
})
