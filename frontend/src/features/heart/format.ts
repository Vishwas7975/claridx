import type { FeatureSpec } from '../../api/types'

export function fieldLabel(spec: FeatureSpec): string {
  return spec.unit ? `${spec.label} (${spec.unit})` : spec.label
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

/** A signed number with a real minus sign; exact zeros carry no sign. */
export function formatSigned(value: number, digits = 3): string {
  const text = Math.abs(value).toFixed(digits)
  if (Number(text) === 0) return text
  return value < 0 ? `\u2212${text}` : `+${text}`
}

/** A patient value in words: option labels for categories, units for numbers. */
export function describeValue(spec: FeatureSpec | undefined, value: number | null): string {
  if (value === null) return 'not provided'
  if (spec === undefined) return String(value)
  if (spec.kind === 'category') {
    return spec.options.find((option) => option.value === value)?.label ?? String(value)
  }
  return spec.unit ? `${value} ${spec.unit}` : String(value)
}
