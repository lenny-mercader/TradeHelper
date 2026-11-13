// Every `close` / `high_52w` / ... is in EUR; `close_local` is in the instrument's `currency`.

export type Quote = {
  symbol: string
  name: string | null
  exchange: string | null
  currency: string | null
  date: string | null
  close: number | null
  close_local: number | null
  change_percent: number | null
  volume: number | null
  followed: boolean
  favorite: boolean
}

export type HistoryPoint = {
  date: string
  close: number | null
  close_local: number
  volume: number
}

export type SearchResult = {
  symbol: string
  name: string | null
  exchange: string | null
  type: string | null
}

export type Mover = {
  symbol: string
  name: string | null
  date: string
  close: number | null
  close_local: number
  currency: string
  change_percent: number
  volume: number
}

export type Movers = {
  date: string | null
  gainers: Mover[]
  losers: Mover[]
}

export type CompareRow = {
  symbol: string
  name: string | null
  currency: string | null
  close: number | null
  perf_1m: number | null
  perf_1y: number | null
  perf_5y: number | null
  volatility_1y: number | null
  high_52w: number | null
  low_52w: number | null
  error: string | null
}

export type Period = '1M' | '6M' | '1Y' | '5Y'

export type PerformanceSeries = {
  symbol: string
  name: string | null
  currency: string | null
  /** Change in % (EUR) since the period start, aligned on Performance.dates. */
  values: (number | null)[]
}

export type Performance = {
  period: Period
  start: string | null
  end: string | null
  dates: string[]
  series: PerformanceSeries[]
  errors: Record<string, string>
}

export type NewsArticle = {
  title: string
  url: string
  published_at: string | null
  image_url: string | null
}

export type NewsFeed = {
  id: string
  name: string
  site_url: string
  logo_url: string
  articles: NewsArticle[]
  error: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = (await res.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // not JSON: keep the status
    }
    throw new Error(detail)
  }
  return (res.status === 204 ? undefined : res.json()) as Promise<T>
}

const enc = encodeURIComponent

export const api = {
  search: (q: string, signal?: AbortSignal) =>
    request<SearchResult[]>(`/api/search?q=${enc(q)}`, { signal }),
  instrument: (symbol: string) => request<Quote>(`/api/instruments/${enc(symbol)}`),
  history: (symbol: string) => request<HistoryPoint[]>(`/api/instruments/${enc(symbol)}/history`),
  watchlist: () => request<Quote[]>('/api/watchlist'),
  follow: (symbol: string) => request<Quote>(`/api/watchlist/${enc(symbol)}`, { method: 'POST' }),
  unfollow: (symbol: string) =>
    request<void>(`/api/watchlist/${enc(symbol)}`, { method: 'DELETE' }),
  favorite: (symbol: string) =>
    request<Quote>(`/api/watchlist/${enc(symbol)}/favorite`, { method: 'POST' }),
  unfavorite: (symbol: string) =>
    request<Quote>(`/api/watchlist/${enc(symbol)}/favorite`, { method: 'DELETE' }),
  movers: () => request<Movers>('/api/market/movers'),
  compare: (symbols: string[]) =>
    request<CompareRow[]>(`/api/compare?symbols=${enc(symbols.join(','))}`),
  performance: (symbols: string[], period: Period) =>
    request<Performance>(`/api/performance?symbols=${enc(symbols.join(','))}&period=${period}`),
  news: (limit: number) => request<NewsFeed[]>(`/api/news?limit=${limit}`),
}
