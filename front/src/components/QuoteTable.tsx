import { Link } from 'react-router'
import type { Quote } from '../api'
import { formatDate, formatEur, formatLocal, formatPercent, trendClass } from '../format'

const MAX_FAVORITES = 5

type Props = {
  quotes: Quote[]
  onRemove?: (symbol: string) => void
  onToggleFavorite?: (symbol: string, favorite: boolean) => void
}

export function QuoteTable({ quotes, onRemove, onToggleFavorite }: Props) {
  const favoriteCount = quotes.filter((q) => q.favorite).length

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {onToggleFavorite && <th />}
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
          {quotes.map((q) => {
            const disabled = !q.favorite && favoriteCount >= MAX_FAVORITES
            return (
              <tr key={q.symbol}>
                {onToggleFavorite && (
                  <td className="favorite-cell">
                    <button
                      type="button"
                      className="star-button"
                      aria-pressed={q.favorite}
                      disabled={disabled}
                      title={disabled ? `${MAX_FAVORITES} favoris maximum` : undefined}
                      onClick={() => onToggleFavorite(q.symbol, !q.favorite)}
                    >
                      {q.favorite ? '★' : '☆'}
                    </button>
                  </td>
                )}
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
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
