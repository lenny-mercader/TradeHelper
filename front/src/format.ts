const price = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const volume = new Intl.NumberFormat('fr-FR', { notation: 'compact', maximumFractionDigits: 1 })
const date = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeZone: 'UTC' })

export const formatPrice = (n: number) => price.format(n)
export const formatVolume = (n: number) => volume.format(n)
export const formatDate = (iso: string) => date.format(new Date(iso))

export const formatSigned = (n: number | null, suffix = '') =>
  n === null ? '—' : `${n > 0 ? '+' : ''}${price.format(n)}${suffix}`
