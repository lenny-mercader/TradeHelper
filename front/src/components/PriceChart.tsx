import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HistoryPoint } from '../api'
import { formatDate, formatPrice } from '../format'

type Props = {
  symbol: string
  history: HistoryPoint[]
}

export function PriceChart({ symbol, history }: Props) {
  return (
    <section className="chart">
      <h2>{symbol} — clôtures sur {history.length} séances</h2>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={history} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
          <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={40} stroke="var(--muted)" />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={formatPrice}
            width={70}
            stroke="var(--muted)"
          />
          <Tooltip
            labelFormatter={(label) => formatDate(String(label))}
            formatter={(value) => [formatPrice(Number(value)), 'Clôture']}
            contentStyle={{ background: 'var(--surface)', border: '1px solid var(--grid)' }}
          />
          <Line type="monotone" dataKey="close" stroke="var(--accent)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
