import { describe, expect, it } from 'vitest'
import { heartFixture } from '../../test/fixtures'
import { describeValue, fieldLabel, formatPercent, formatSigned } from './format'

function featureSpec(name: string) {
  const found = heartFixture.features.find((spec) => spec.name === name)
  if (found === undefined) throw new Error(`feature ${name} missing from the fixture`)
  return found
}

describe('formatting', () => {
  it('formats signed numbers with a real minus sign and no sign for zero', () => {
    expect(formatSigned(0.146)).toBe('+0.146')
    expect(formatSigned(-0.159)).toBe('\u22120.159')
    expect(formatSigned(-0.0001)).toBe('0.000')
    expect(formatSigned(0)).toBe('0.000')
  })

  it('formats probabilities as percentages', () => {
    expect(formatPercent(0.615)).toBe('61.5%')
    expect(formatPercent(0.996, 0)).toBe('100%')
  })

  it('describes values in words', () => {
    expect(describeValue(featureSpec('cp'), 4)).toBe('Asymptomatic')
    expect(describeValue(featureSpec('age'), 59)).toBe('59 years')
    expect(describeValue(featureSpec('oldpeak'), 2)).toBe('2')
    expect(describeValue(featureSpec('age'), null)).toBe('not provided')
    expect(describeValue(undefined, 3)).toBe('3')
  })

  it('adds the unit to labels that have one', () => {
    expect(fieldLabel(featureSpec('chol'))).toBe('Serum cholesterol (mg/dl)')
    expect(fieldLabel(featureSpec('sex'))).toBe('Sex')
  })
})
