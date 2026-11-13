const eur = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })
const number = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 })
const compact = new Intl.NumberFormat('fr-FR', { notation: 'compact', maximumFractionDigits: 1 })
const date = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeZone: 'UTC' })

const DASH = '—'

export const formatEur = (n: number | null | undefined) => (n == null ? DASH : eur.format(n))

export function formatLocal(n: number | null | undefined, currency: string | null | undefined) {
  if (n == null) return DASH
  if (!currency) return number.format(n)
  try {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(n)
  } catch {
    return `${number.format(n)} ${currency}`
  }
}

export const formatPercent = (n: number | null | undefined) =>
  n == null ? DASH : `${n > 0 ? '+' : ''}${number.format(n)} %`

export const formatRatio = (n: number | null | undefined) =>
  n == null ? DASH : `${number.format(n)} %`

export const formatVolume = (n: number | null | undefined) => (n == null ? DASH : compact.format(n))

export const formatDate = (iso: string | null | undefined) =>
  iso ? date.format(new Date(iso)) : DASH

export const trendClass = (n: number | null | undefined) =>
  n == null || n === 0 ? '' : n > 0 ? 'up' : 'down'

const relative = new Intl.RelativeTimeFormat('fr-FR', { numeric: 'auto' })
const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

/** "il y a 12 min" / "il y a 3 h" for a recent timestamp, falling back to the date beyond a week. */
export function formatRelativeDate(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 0 || diff > 7 * DAY) return formatDate(iso)
  if (diff < HOUR) return relative.format(-Math.round(diff / MINUTE), 'minute')
  if (diff < DAY) return relative.format(-Math.round(diff / HOUR), 'hour')
  return relative.format(-Math.round(diff / DAY), 'day')
}
