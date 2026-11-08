import { Link, useSearchParams } from 'react-router'
import { api, type CompareRow } from '../api'
import { SearchBox } from '../components/SearchBox'
import { Status } from '../components/Status'
import { formatEur, formatPercent, formatRatio, trendClass } from '../format'
import { useApi } from '../hooks/useApi'

const MAX = 10

type Metric = {
  label: string
  value: (r: CompareRow) => number | null
  format: (n: number | null) => string
  colored?: boolean
  best?: 'max' | 'min'
}

const METRICS: Metric[] = [
  { label: 'Clôture (EUR)', value: (r) => r.close, format: formatEur },
  { label: 'Perf. 1 mois', value: (r) => r.perf_1m, format: formatPercent, colored: true, best: 'max' },
  { label: 'Perf. 1 an', value: (r) => r.perf_1y, format: formatPercent, colored: true, best: 'max' },
  { label: 'Perf. 5 ans', value: (r) => r.perf_5y, format: formatPercent, colored: true, best: 'max' },
  {
    label: 'Volatilité 1 an',
    value: (r) => r.volatility_1y,
    format: formatRatio,
    best: 'min',
  },
  { label: 'Plus haut 52 sem.', value: (r) => r.high_52w, format: formatEur },
  { label: 'Plus bas 52 sem.', value: (r) => r.low_52w, format: formatEur },
]

function bestValue(rows: CompareRow[], metric: Metric): number | null {
  const values = rows.map(metric.value).filter((v): v is number => v != null)
  if (!metric.best || values.length < 2) return null
  return metric.best === 'max' ? Math.max(...values) : Math.min(...values)
}

export function ComparePage() {
  const [params, setParams] = useSearchParams()
  const symbols = (params.get('s') ?? '')
    .split(',')
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, MAX)
  const key = symbols.join(',')
  const data = useApi(key || null, () => api.compare(symbols))

  const setSymbols = (next: string[]) => setParams(next.length ? { s: next.join(',') } : {})
  const rows = data.data ?? []

  return (
    <>
      <h1>Comparateur</h1>
      <p className="muted">Toutes les valeurs sont en EUR (conversion au taux BCE du jour de chaque séance).</p>

      <div className="toolbar">
        {symbols.length < MAX && (
          <SearchBox
            placeholder="Ajouter une action à comparer…"
            onSelect={(r) => !symbols.includes(r.symbol) && setSymbols([...symbols, r.symbol])}
          />
        )}
      </div>

      {symbols.length === 0 && <p className="muted">Ajoute au moins une action.</p>}
      <Status
        loading={data.loading}
        error={data.error}
        loadingText="Calcul… (les actions jamais ouvertes sont chargées au passage)"
      />

      {rows.length > 0 && (
        <div className="table-wrap">
          <table className="data compare">
            <thead>
              <tr>
                <th />
                {rows.map((r) => (
                  <th key={r.symbol}>
                    <Link to={`/stock/${encodeURIComponent(r.symbol)}`}>{r.symbol}</Link>
                    <button
                      type="button"
                      className="link"
                      title="Retirer"
                      onClick={() => setSymbols(symbols.filter((s) => s !== r.symbol))}
                    >
                      ×
                    </button>
                    <div className="name">{r.name ?? ''}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {METRICS.map((m) => {
                const best = bestValue(rows, m)
                return (
                  <tr key={m.label}>
                    <th>{m.label}</th>
                    {rows.map((r) => {
                      const v = m.value(r)
                      const classes = [
                        m.colored ? trendClass(v) : '',
                        best !== null && v === best ? 'best' : '',
                      ].join(' ')
                      return (
                        <td key={r.symbol} className={classes}>
                          {r.error ? (m === METRICS[0] ? <span className="error">{r.error}</span> : '') : m.format(v)}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
