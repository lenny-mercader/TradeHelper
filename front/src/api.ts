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

export type HeatmapTile = {
  symbol: string
  name: string | null
  close: number | null
  close_local: number
  currency: string
  change_percent: number
  volume: number
  dollar_volume: number
}

export type Heatmap = {
  date: string | null
  tiles: HeatmapTile[]
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

export type Vix = {
  value: number
  label: string
}

export type InstrumentProfile = {
  is_us: boolean
  sector: string | null
  industry: string | null
  summary: string | null
  country: string | null
  website: string | null
  employees: number | null
  market_cap: number | null
  trailing_pe: number | null
  forward_pe: number | null
  enterprise_value: number | null
  price_to_book: number | null
  profit_margin: number | null
  return_on_equity: number | null
  debt_to_equity: number | null
  eps: number | null
  recommendation: string | null
  target_mean_price: number | null
  analyst_count: number | null
  dividend_yield: number | null
  week52_high: number | null
  week52_low: number | null
  average_volume: number | null
  transactions_today: number | null
  vix: Vix | null
}

export type CatalogRow = {
  symbol: string
  name: string | null
  country: string | null
  sector: string | null
  currency: string | null
  close: number | null
  change_percent: number | null
  market_cap: number | null
}

export type CatalogPage = {
  rows: CatalogRow[]
  total: number
  page: number
  page_size: number
}

export type CatalogFacets = {
  countries: string[]
  sectors: string[]
}

export type CatalogSort = 'change' | 'market_cap' | 'name'

export type CatalogFilters = {
  q?: string
  countries?: string[]
  sector?: string
  sort: CatalogSort
  order: 'asc' | 'desc'
  page: number
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
  profile: (symbol: string) =>
    request<InstrumentProfile>(`/api/instruments/${enc(symbol)}/profile`),
  watchlist: () => request<Quote[]>('/api/watchlist'),
  follow: (symbol: string) => request<Quote>(`/api/watchlist/${enc(symbol)}`, { method: 'POST' }),
  unfollow: (symbol: string) =>
    request<void>(`/api/watchlist/${enc(symbol)}`, { method: 'DELETE' }),
  favorite: (symbol: string) =>
    request<Quote>(`/api/watchlist/${enc(symbol)}/favorite`, { method: 'POST' }),
  unfavorite: (symbol: string) =>
    request<Quote>(`/api/watchlist/${enc(symbol)}/favorite`, { method: 'DELETE' }),
  movers: () => request<Movers>('/api/market/movers'),
  heatmap: (limit = 100) => request<Heatmap>(`/api/market/heatmap?limit=${limit}`),
  compare: (symbols: string[]) =>
    request<CompareRow[]>(`/api/compare?symbols=${enc(symbols.join(','))}`),
  performance: (symbols: string[], period: Period) =>
    request<Performance>(`/api/performance?symbols=${enc(symbols.join(','))}&period=${period}`),
  news: (limit: number) => request<NewsFeed[]>(`/api/news?limit=${limit}`),
  catalogFacets: () => request<CatalogFacets>('/api/catalog/facets'),
  catalog: (filters: CatalogFilters) => {
    const params = new URLSearchParams()
    if (filters.q) params.set('q', filters.q)
    for (const c of filters.countries ?? []) params.append('country', c)
    if (filters.sector) params.set('sector', filters.sector)
    params.set('sort', filters.sort)
    params.set('order', filters.order)
    params.set('page', String(filters.page))
    return request<CatalogPage>(`/api/catalog?${params.toString()}`)
  },
}
