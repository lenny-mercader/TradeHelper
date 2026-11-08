import { Link } from 'react-router'
import type { Quote } from '../api'
import { formatDate, formatEur, formatLocal, formatPercent, trendClass } from '../format'

type Props = {
  quotes: Quote[]
  onRemove?: (symbol: string) => void
}

export function QuoteTable({ quotes, onRemove }: Props) {
  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            <th>Symbole</th>
            <th>Nom</th>
            <th>Clôture (EUR)</th>
            <th>Variation</th>
            <th>Prix local</th>
            <th>Date</th>
            {onRemove && <th />}
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => (
            <tr key={q.symbol}>
              <td className="symbol">
                <Link to={`/stock/${encodeURIComponent(q.symbol)}`}>{q.symbol}</Link>
              </td>
              <td className="name">{q.name ?? ''}</td>
              <td>{formatEur(q.close)}</td>
              <td className={trendClass(q.change_percent)}>{formatPercent(q.change_percent)}</td>
              <td className="muted">{formatLocal(q.close_local, q.currency)}</td>
              <td className="muted">{formatDate(q.date)}</td>
              {onRemove && (
                <td>
                  <button type="button" className="link" onClick={() => onRemove(q.symbol)}>
                    Retirer
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
