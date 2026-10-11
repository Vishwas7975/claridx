import { describe, expect, it } from 'vitest'
import { heartFixture } from '../../test/fixtures'
import { EXAMPLES } from './examples'
import { MIN_MEASUREMENTS, buildPatient, fieldError, toFormValues, validateForm } from './form'

const specs = heartFixture.features
const numberSpecs = specs.filter((spec) => spec.kind === 'number')
const categorySpecs = specs.filter((spec) => spec.kind === 'category')

function featureSpec(name: string) {
  const found = specs.find((spec) => spec.name === name)
  if (found === undefined) throw new Error(`feature ${name} missing from the fixture`)
  return found
}

describe('form rules mirror the backend', () => {
  it('requires the same minimum number of measurements as the API', () => {
    expect(MIN_MEASUREMENTS).toBe(heartFixture.min_measurements)
  })

  it.each(numberSpecs.map((spec) => [spec.name, spec] as const))(
    '%s accepts its bounds and rejects values outside them',
    (_name, spec) => {
      const step = spec.step ?? 1
      expect(fieldError(spec, String(spec.minimum))).toBeNull()
      expect(fieldError(spec, String(spec.maximum))).toBeNull()
      expect(fieldError(spec, String((spec.minimum ?? 0) - step))).not.toBeNull()
      expect(fieldError(spec, String((spec.maximum ?? 0) + step))).not.toBeNull()
    },
  )

  it.each(categorySpecs.map((spec) => [spec.name, spec] as const))(
    '%s accepts only its listed options',
    (_name, spec) => {
      const allowed = new Set(spec.options.map((option) => option.value))
      for (let candidate = -1; candidate <= 9; candidate += 1) {
        expect(fieldError(spec, String(candidate)) === null).toBe(allowed.has(candidate))
      }
    },
  )

  it('rejects decimals for whole-number features but not for decimal ones', () => {
    expect(fieldError(featureSpec('age'), '54.5')).toBe('Enter a whole number')
    expect(fieldError(featureSpec('oldpeak'), '1.5')).toBeNull()
  })

  it('treats blank input as not provided and flags non-numeric text', () => {
    const age = featureSpec('age')
    expect(fieldError(age, '')).toBeNull()
    expect(fieldError(age, '   ')).toBeNull()
    expect(fieldError(age, 'abc')).toBe('Enter a number')
  })
})

describe('building the request', () => {
  it('keeps only valid, non-blank values, as numbers', () => {
    const patient = buildPatient(specs, {
      age: '54',
      sex: '1',
      oldpeak: '1.5',
      chol: '',
      thalach: 'abc',
      trestbps: '999',
    })
    expect(patient).toEqual({ age: 54, sex: 1, oldpeak: 1.5 })
  })

  it('allows submitting only with enough valid measurements and no errors', () => {
    const full = toFormValues(EXAMPLES[0].values)
    const entries = Object.entries(full)
    const some = (count: number) => Object.fromEntries(entries.slice(0, count))

    expect(validateForm(specs, some(MIN_MEASUREMENTS - 1)).canSubmit).toBe(false)
    expect(validateForm(specs, some(MIN_MEASUREMENTS)).canSubmit).toBe(true)

    const withMistake = validateForm(specs, { ...full, age: '130' })
    expect(withMistake.errors).toEqual({ age: 'Must be at most 120' })
    expect(withMistake.canSubmit).toBe(false)
  })
})

describe('examples', () => {
  it.each(EXAMPLES.map((example) => [example.id, example] as const))(
    '%s uses only real features and can be submitted',
    (_id, example) => {
      const known = new Set(specs.map((spec) => spec.name))
      for (const name of Object.keys(example.values)) expect(known.has(name)).toBe(true)

      const result = validateForm(specs, toFormValues(example.values))
      expect(result.errors).toEqual({})
      expect(result.canSubmit).toBe(true)
    },
  )
})
