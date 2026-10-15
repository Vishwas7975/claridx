import type { FeatureSpec } from '../../api/types'
import { SUSPICIOUS_ZERO_FEATURES } from './form'

export { describeShare, formatPercent, formatSigned, wholePercent } from '../heart/format'

export function fieldLabel(spec: FeatureSpec): string {
  return spec.unit ? `${spec.label} (${spec.unit})` : spec.label
}

/** A patient value in words: units for numbers, explicit unmeasured for suspicious zeros. */
export function describeValue(spec: FeatureSpec | undefined, value: number | null): string {
  if (value === null) return 'not provided'
  if (spec === undefined) return String(value)
  if (SUSPICIOUS_ZERO_FEATURES.has(spec.name) && value === 0) {
    return 'unmeasured'
  }
  return spec.unit ? `${value} ${spec.unit}` : String(value)
}
