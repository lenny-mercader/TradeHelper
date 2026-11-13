import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, type Period } from '../api'
import { formatDate, formatPercent } from '../format'
import { useApi } from '../hooks/useApi'
import { Status } from './Status'

const PERIODS: { value: Period; label: string }[] = [
  { value: '1M', label: '1M' },
  { value: '6M', label: '6M' },
  { value: '1Y', label: '1A' },
  { value: '5Y', label: '5A' },
]

type Props = {
  symbols: string[]
  period: Period
  onPeriodChange: (period: Period) => void
  /** CSS color of each symbol's line (colors follow the symbol, not its position). */
  colorOf: (symbol: string) => string
}

type Row = { date: string } & Record<string, number | null | string>

/**
 * Cumulative change (EUR, %) of several instruments over a period, on one shared axis.
 * Reusable: the watchlist chart today, the comparator later.
 */
export function PerformanceChart({ symbols, period, onPeriodChange, colorOf }: Props) {
  const key = symbols.length ? `${symbols.join(',')}|${period}` : null
  const data = useApi(key, () => api.performance(symbols, period))
  const [hovered, setHovered] = useState<number | null>(null)

  // Recharts reads dotted keys as paths ("MC.PA"), so series are keyed by index.
  const rows = useMemo<Row[]>(() => {
    const perf = data.data
    if (!perf) return []
    return perf.dates.map((date, i) => {
      const row: Row = { date }
      perf.series.forEach((s, j) => {
        row[`s${j}`] = s.values[i]
      })
      return row
    })
  }, [data.data])

  const series = data.data?.series ?? []
  const errors = Object.entries(data.data?.errors ?? {})

  return (
    <section className="perf-chart">
      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Période">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              type="button"
              aria-pressed={p.value === period}
              onClick={() => onPeriodChange(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <span className="muted">Variation en EUR depuis le début de la période</span>
      </div>

      {symbols.length === 0 && <p className="muted">Coche au moins une action.</p>}
      <Status loading={data.loading} error={data.error} />
      {errors.length > 0 && (
        <p className="error">
          {errors.map(([symbol, reason]) => `${symbol} : ${reason}`).join(' · ')}
        </p>
      )}

      {rows.length > 0 && (
        <div className="perf-chart-plot" onMouseLeave={() => setHovered(null)}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                minTickGap={60}
                stroke="var(--muted)"
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v: number) => formatPercent(v)}
                width={72}
                stroke="var(--muted)"
                tickLine={false}
                axisLine={false}
              />
              <ReferenceLine y={0} stroke="var(--muted)" />
              <Tooltip
                cursor={{ stroke: 'var(--muted)', strokeDasharray: '3 3' }}
                content={({ active, payload, label }) => {
                  if (!active || hovered === null || !payload) return null
                  const s = series[hovered]
                  const item = payload.find((p) => p.dataKey === `s${hovered}`)
                  if (!s || !item || item.value == null) return null
                  return (
                    <div className="chart-tooltip">
                      <div className="muted">{formatDate(String(label))}</div>
                      <div>
                        <span className="swatch" style={{ background: colorOf(s.symbol) }} />
                        <strong>{s.symbol}</strong> {s.name ?? ''}
                      </div>
                      <strong>{formatPercent(Number(item.value))}</strong>
                    </div>
                  )
                }}
              />
              {series.map((s, j) => (
                <Line
                  key={s.symbol}
                  dataKey={`s${j}`}
                  name={s.symbol}
                  stroke={colorOf(s.symbol)}
                  strokeWidth={2}
                  dot={false}
                  activeDot={hovered === j ? { r: 4 } : false}
                  isAnimationActive={false}
                  connectNulls={false}
                />
              ))}
              {/* Wide invisible copies of each line: the hover target for "which curve". */}
              {series.map((s, j) => (
                <Line
                  key={`${s.symbol}-hit`}
                  dataKey={`s${j}`}
                  stroke="transparent"
                  strokeWidth={14}
                  dot={false}
                  activeDot={false}
                  isAnimationActive={false}
                  legendType="none"
                  onMouseEnter={() => setHovered(j)}
                  onMouseLeave={() => setHovered(null)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}
