import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HistoryPoint } from '../api'
import { formatDate, formatEur } from '../format'

type Props = {
  history: HistoryPoint[]
}

export function PriceChart({ history }: Props) {
  const points = history.filter((p) => p.close !== null)
  return (
    <section className="panel">
      <h2>Clôtures en EUR — {points.length} séances</h2>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
          <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={50} stroke="var(--muted)" />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(v: number) => formatEur(v)}
            width={90}
            stroke="var(--muted)"
          />
          <Tooltip
            labelFormatter={(label) => formatDate(String(label))}
            formatter={(value) => [formatEur(Number(value)), 'Clôture']}
            contentStyle={{ background: 'var(--surface)', border: '1px solid var(--grid)' }}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="var(--accent)"
            dot={false}
            strokeWidth={2}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
