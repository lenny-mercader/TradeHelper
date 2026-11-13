import { Link } from 'react-router'
import type { Quote } from '../api'
import { MiniQuoteList } from './MiniQuoteList'

const TOP_N = 5

/**
 * Top 5 gainers / top 5 losers / favorites, from the signed-in user's watchlist.
 * No stock appears in both the gainers and losers blocks: losers are picked from what's
 * left after the gainers are removed, so the two never overlap even with a small watchlist.
 */
function splitGainersLosers(quotes: Quote[]) {
  const ranked = quotes
    .filter((q) => q.change_percent != null)
    .sort((a, b) => (b.change_percent ?? 0) - (a.change_percent ?? 0))
  const gainers = ranked.slice(0, TOP_N)
  const rest = ranked.slice(TOP_N)
  const losers = rest.slice(-TOP_N).reverse()
  return { gainers, losers }
}

type Props = {
  quotes: Quote[]
}

export function WatchlistSummaryPanel({ quotes }: Props) {
  const { gainers, losers } = splitGainersLosers(quotes)
  const favorites = quotes.filter((q) => q.favorite)

  return (
    <aside className="watchlist-panel">
      <div className="watchlist-panel-head">
        <h2>Mes actions suivies</h2>
        <Link className="button secondary" to="/watchlist">
          Voir la liste des valeurs suivies
        </Link>
      </div>

      {quotes.length === 0 ? (
        <p className="muted">
          Aucune action suivie. Cherche une action et ajoute-la à ta liste.
        </p>
      ) : (
        <>
          <MiniQuoteList title="Top 5 gagnantes" quotes={gainers} emptyText="Pas encore de données." />
          <MiniQuoteList title="Top 5 perdantes" quotes={losers} emptyText="Pas encore de données." />
          <MiniQuoteList
            title="Favoris"
            quotes={favorites}
            emptyText="Aucun favori. Marque des actions depuis la liste de suivi."
          />
        </>
      )}
    </aside>
  )
}
