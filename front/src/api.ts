export type Quote = {
  symbol: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  change: number | null
  change_percent: number | null
}

export type HistoryPoint = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`HTTP ${res.status} sur ${path}`)
  return res.json() as Promise<T>
}

export const fetchQuotes = () => getJson<Quote[]>('/api/quotes')

export const fetchHistory = (symbol: string) =>
  getJson<HistoryPoint[]>(`/api/quotes/${encodeURIComponent(symbol)}/history`)
