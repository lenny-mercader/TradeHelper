import { useAuth } from '@clerk/react'
import { Link } from 'react-router'
import { api, type Mover } from '../api'
import { NewsSection } from '../components/NewsSection'
import { SignInPrompt } from '../components/SignInPrompt'
import { Status } from '../components/Status'
import { WatchlistSummaryPanel } from '../components/WatchlistSummaryPanel'
import { formatDate, formatEur, formatPercent, formatVolume, trendClass } from '../format'
import { useApi } from '../hooks/useApi'

function MoversTable({ title, movers }: { title: string; movers: Mover[] }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {movers.length === 0 ? (
        <p className="muted">Pas encore de données.</p>
      ) : (
        // table-wrap scrolls horizontally instead of overflowing the panel/page on long names.
        <div className="table-wrap no-margin">
          <table className="data compact">
            <tbody>
              {movers.map((m) => (
                <tr key={m.symbol}>
                  <td className="symbol">
                    <Link to={`/stock/${encodeURIComponent(m.symbol)}`}>{m.symbol}</Link>
                  </td>
                  <td className="name">{m.name ?? ''}</td>
                  <td>{formatEur(m.close)}</td>
                  <td className={trendClass(m.change_percent)}>
                    {formatPercent(m.change_percent)}
                  </td>
                  <td className="muted">{formatVolume(m.volume)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export function MarketPage() {
  const { isLoaded, isSignedIn, userId } = useAuth()
  const movers = useApi('movers', api.movers)
  // Keyed by user: signing in/out reloads the right list.
  const watchlist = useApi(isSignedIn ? `watchlist:${userId}` : null, api.watchlist)

  return (
    <>
      <div className="home-layout">
        <div className="home-main">
          <h1>Marché US</h1>
          <p className="muted">
            Plus fortes variations de la séance du {formatDate(movers.data?.date)} (actions &gt; 1
            $, volume &gt; 200 k, hors splits).
          </p>
          <Status loading={movers.loading} error={movers.error} />
          {movers.data && (
            <div className="grid-2">
              <MoversTable title="Plus fortes hausses" movers={movers.data.gainers} />
              <MoversTable title="Plus fortes baisses" movers={movers.data.losers} />
            </div>
          )}
        </div>

        {isLoaded && !isSignedIn && (
          <aside className="watchlist-panel">
            <h2>Mes actions suivies</h2>
            <SignInPrompt />
          </aside>
        )}
        {isSignedIn && (
          <>
            <Status loading={watchlist.loading} error={watchlist.error} />
            {watchlist.data && <WatchlistSummaryPanel quotes={watchlist.data} />}
          </>
        )}
      </div>

      <NewsSection limit={5} />
    </>
  )
}
