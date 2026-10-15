import { describe, expect, it } from 'vitest'
import { diabetesFixture } from '../../test/fixtures'
import { EXAMPLES } from './examples'
import {
  MIN_MEASUREMENTS,
  SUSPICIOUS_ZERO_FEATURES,
  buildPatient,
  countEffectiveMeasurements,
  fieldError,
  isEffectiveMeasurement,
  toFormValues,
  validateForm,
} from './form'
import { describeValue, fieldLabel } from './format'

const specs = diabetesFixture.features

function featureSpec(name: string) {
  const found = specs.find((spec) => spec.name === name)
  if (found === undefined) throw new Error(`feature ${name} missing from diabetes fixture`)
  return found
}

describe('diabetes form rules mirror the backend', () => {
  it('requires the same minimum number of effective measurements as the API', () => {
    expect(MIN_MEASUREMENTS).toBe(diabetesFixture.min_measurements)
    expect(MIN_MEASUREMENTS).toBe(5)
  })

  it('verifies suspicious zero features list matches backend definition', () => {
    expect(Array.from(SUSPICIOUS_ZERO_FEATURES).sort()).toEqual([
      'insu',
      'mass',
      'plas',
      'pres',
      'skin',
    ])
  })

  it.each(specs.map((spec) => [spec.name, spec] as const))(
    '%s accepts its bounds and rejects values outside them',
    (_name, spec) => {
      const step = spec.step ?? 1
      expect(fieldError(spec, String(spec.minimum))).toBeNull()
      expect(fieldError(spec, String(spec.maximum))).toBeNull()
      if (spec.minimum !== null) {
        expect(fieldError(spec, String(spec.minimum - step))).toBe(
          `Must be at least ${spec.minimum}`,
        )
      }
      if (spec.maximum !== null) {
        expect(fieldError(spec, String(spec.maximum + step))).toBe(
          `Must be at most ${spec.maximum}`,
        )
      }
    },
  )

  it('strictly enforces age >= 21 as cohort inclusion boundary', () => {
    const age = featureSpec('age')
    expect(fieldError(age, '20')).toBe('Must be at least 21')
    expect(fieldError(age, '21')).toBeNull()
    expect(fieldError(age, '120')).toBeNull()
    expect(fieldError(age, '121')).toBe('Must be at most 120')
  })

  it('rejects decimals for whole-number features but allows decimal features', () => {
    expect(fieldError(featureSpec('preg'), '2.5')).toBe('Enter a whole number')
    expect(fieldError(featureSpec('plas'), '120.4')).toBe('Enter a whole number')
    expect(fieldError(featureSpec('age'), '35.5')).toBe('Enter a whole number')
    expect(fieldError(featureSpec('mass'), '28.5')).toBeNull()
    expect(fieldError(featureSpec('pedi'), '0.345')).toBeNull()
  })

  it('treats blank input as not provided and flags malformed or non-finite text', () => {
    const plas = featureSpec('plas')
    expect(fieldError(plas, '')).toBeNull()
    expect(fieldError(plas, '   ')).toBeNull()
    expect(fieldError(plas, 'abc')).toBe('Enter a number')
    expect(fieldError(plas, 'NaN')).toBe('Enter a number')
    expect(fieldError(plas, 'Infinity')).toBe('Enter a number')
    expect(fieldError(plas, '-Infinity')).toBe('Enter a number')
  })
})

describe('effective measurement counting & suspicious zero handling', () => {
  it('counts preg = 0 as an effective measurement', () => {
    expect(isEffectiveMeasurement('preg', 0)).toBe(true)
    const patient = { preg: 0 }
    expect(countEffectiveMeasurements(patient)).toBe(1)
  })

  it.each(['plas', 'pres', 'skin', 'insu', 'mass'])(
    'does not count zero in %s as an effective measurement',
    (feature) => {
      expect(isEffectiveMeasurement(feature, 0)).toBe(false)
      const patient = { [feature]: 0 }
      expect(countEffectiveMeasurements(patient)).toBe(0)
    },
  )

  it.each(['plas', 'pres', 'skin', 'insu', 'mass'])(
    'counts non-zero in %s as an effective measurement',
    (feature) => {
      expect(isEffectiveMeasurement(feature, 10)).toBe(true)
      const patient = { [feature]: 10 }
      expect(countEffectiveMeasurements(patient)).toBe(1)
    },
  )

  it('counts pedi = 0 as effective if within bounds', () => {
    expect(isEffectiveMeasurement('pedi', 0)).toBe(true)
    expect(countEffectiveMeasurements({ pedi: 0 })).toBe(1)
  })
})

describe('building the patient request', () => {
  it('keeps only valid, non-blank values, and omits empty/invalid fields', () => {
    const patient = buildPatient(specs, {
      preg: '2',
      plas: '120',
      pres: '',
      skin: '   ',
      insu: 'invalid',
      mass: '31.5',
      pedi: '0.45',
      age: '40',
    })

    expect(patient).toEqual({
      preg: 2,
      plas: 120,
      mass: 31.5,
      pedi: 0.45,
      age: 40,
    })
    expect(patient.pres).toBeUndefined()
    expect(patient.skin).toBeUndefined()
    expect(patient.insu).toBeUndefined()
  })

  it('allows submitting with exactly 5 effective measurements, but not 4', () => {
    const fourValues = {
      preg: '2',
      plas: '130',
      pres: '80',
      age: '30',
    }
    const resultFour = validateForm(specs, fourValues)
    expect(resultFour.provided).toBe(4)
    expect(resultFour.canSubmit).toBe(false)

    const fiveValues = {
      ...fourValues,
      mass: '28.0',
    }
    const resultFive = validateForm(specs, fiveValues)
    expect(resultFive.provided).toBe(5)
    expect(resultFive.canSubmit).toBe(true)
  })

  it('rejects submission if 5 measurements are provided but one is a suspicious zero', () => {
    const valuesWithZero = {
      preg: '2',
      plas: '0', // suspicious zero! Does not count
      pres: '80',
      mass: '28.0',
      age: '30',
    }
    const result = validateForm(specs, valuesWithZero)
    expect(result.errors).toEqual({})
    expect(result.provided).toBe(4) // 4 effective, not 5
    expect(result.canSubmit).toBe(false)
  })

  it('accepts submission if 5 measurements are provided including preg = 0', () => {
    const valuesWithPregZero = {
      preg: '0', // valid pregnancy count!
      plas: '120',
      pres: '80',
      mass: '28.0',
      age: '30',
    }
    const result = validateForm(specs, valuesWithPregZero)
    expect(result.errors).toEqual({})
    expect(result.provided).toBe(5)
    expect(result.canSubmit).toBe(true)
  })

  it('prevents submission if any field has a validation error', () => {
    const full = toFormValues(EXAMPLES[0].values)
    const withError = validateForm(specs, { ...full, age: '15' })
    expect(withError.errors).toEqual({ age: 'Must be at least 21' })
    expect(withError.canSubmit).toBe(false)
  })

  it('editing a value from 0 to non-zero increases effective measurement count', () => {
    const values = {
      preg: '1',
      plas: '0',
      pres: '70',
      mass: '25.0',
      age: '30',
    }
    const initial = validateForm(specs, values)
    expect(initial.provided).toBe(4)
    expect(initial.canSubmit).toBe(false)

    const updated = validateForm(specs, { ...values, plas: '110' })
    expect(updated.provided).toBe(5)
    expect(updated.canSubmit).toBe(true)
  })
})

describe('diabetes formatting', () => {
  it('formats field labels with units where applicable', () => {
    expect(fieldLabel(featureSpec('plas'))).toBe('Plasma glucose concentration (mg/dL)')
    expect(fieldLabel(featureSpec('mass'))).toBe('Body mass index (kg/m^2)')
    expect(fieldLabel(featureSpec('preg'))).toBe('Number of pregnancies')
  })

  it('describes values with units and notes unmeasured suspicious zeros', () => {
    expect(describeValue(featureSpec('plas'), 140)).toBe('140 mg/dL')
    expect(describeValue(featureSpec('plas'), 0)).toBe('unmeasured')
    expect(describeValue(featureSpec('preg'), 0)).toBe('0')
    expect(describeValue(featureSpec('age'), null)).toBe('not provided')
  })
})

describe('diabetes demo examples', () => {
  it.each(EXAMPLES.map((example) => [example.id, example] as const))(
    '%s meets backend contract bounds and has at least 5 effective measurements',
    (_id, example) => {
      const known = new Set(specs.map((spec) => spec.name))
      for (const name of Object.keys(example.values)) {
        expect(known.has(name)).toBe(true)
      }

      const formValues = toFormValues(example.values)
      const result = validateForm(specs, formValues)
      expect(result.errors).toEqual({})
      expect(result.provided).toBeGreaterThanOrEqual(MIN_MEASUREMENTS)
      expect(result.canSubmit).toBe(true)
    },
  )
})
