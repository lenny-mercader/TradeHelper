import type { Quote } from '../api'
import { formatPrice, formatSigned, formatVolume } from '../format'

type Props = {
  quotes: Quote[]
  selected: string | null
  onSelect: (symbol: string) => void
}

function trendClass(change: number | null) {
  if (change === null || change === 0) return ''
  return change > 0 ? 'up' : 'down'
}

export function QuotesTable({ quotes, selected, onSelect }: Props) {
  return (
    <div className="table-wrap">
      <table className="quotes">
        <thead>
          <tr>
            <th>Symbole</th>
            <th>Clôture</th>
            <th>Variation</th>
            <th>%</th>
            <th>Ouverture</th>
            <th>Haut</th>
            <th>Bas</th>
            <th>Volume</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => (
            <tr
              key={q.symbol}
              className={q.symbol === selected ? 'selected' : undefined}
              onClick={() => onSelect(q.symbol)}
            >
              <td className="symbol">{q.symbol}</td>
              <td>{formatPrice(q.close)}</td>
              <td className={trendClass(q.change)}>{formatSigned(q.change)}</td>
              <td className={trendClass(q.change)}>{formatSigned(q.change_percent, ' %')}</td>
              <td>{formatPrice(q.open)}</td>
              <td>{formatPrice(q.high)}</td>
              <td>{formatPrice(q.low)}</td>
              <td>{formatVolume(q.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
