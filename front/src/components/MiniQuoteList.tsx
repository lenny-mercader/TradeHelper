import { Link } from 'react-router'
import type { Quote } from '../api'
import { formatPercent, trendClass } from '../format'

type Props = {
  title: string
  quotes: Quote[]
  emptyText: string
}

/** Compact ranked list for the homepage watchlist panel (gainers / losers / favorites). */
export function MiniQuoteList({ title, quotes, emptyText }: Props) {
  return (
    <div className="mini-quote-list">
      <h3>{title}</h3>
      {quotes.length === 0 && <p className="muted">{emptyText}</p>}
      {quotes.length > 0 && (
        <ul>
          {quotes.map((q) => (
            <li key={q.symbol}>
              <Link to={`/stock/${encodeURIComponent(q.symbol)}`}>
                <span className="symbol">{q.symbol}</span>
                <span className="name muted">{q.name ?? ''}</span>
                <span className={trendClass(q.change_percent)}>
                  {formatPercent(q.change_percent)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
