import { useAuth } from '@clerk/react'
import { Link } from 'react-router'
import { api, type Mover } from '../api'
import { HeatmapPanel } from '../components/HeatmapPanel'
import { NewsSidebar } from '../components/NewsSidebar'
import { SignInPrompt } from '../components/SignInPrompt'
import { Status } from '../components/Status'
import { WatchlistSummaryPanel } from '../components/WatchlistSummaryPanel'
import { formatDate, formatEur, formatPercent, formatVolume, trendClass } from '../format'
import { useApi } from '../hooks/useApi'
import { useMediaQuery } from '../hooks/useMediaQuery'
import { useStoredState } from '../hooks/useStoredState'

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

type HomeState = {
  newsOpen: boolean
}

// News starts open on desktop; the mobile layout below the breakpoint always starts collapsed
// regardless of this (see the check below), since it would otherwise push everything else down.
const DEFAULT_HOME_STATE: HomeState = { newsOpen: true }

export function MarketPage() {
  const { isLoaded, isSignedIn, userId } = useAuth()
  const movers = useApi('movers', api.movers)
  // Keyed by user: signing in/out reloads the right list.
  const watchlist = useApi(isSignedIn ? `watchlist:${userId}` : null, api.watchlist)
  const [homeState, updateHome] = useStoredState('tradehelper:home', DEFAULT_HOME_STATE)
  // Starts collapsed on mobile regardless of the stored preference: it would otherwise push
  // everything else down a phone screen. Reacts live to resizing, not just the page load width.
  const isMobile = useMediaQuery('(max-width: 767px)')
  const newsOpen = homeState.newsOpen && !isMobile

  return (
    <>
      <h1>Marché US</h1>

      {/* Reopening lives right where the sidebar itself would be, not off in the page header:
          hidden on mobile too, since the sidebar never shows there (see `newsOpen` below) —
          the "Actualité" nav tab covers mobile instead. */}
      {!isMobile && !newsOpen && (
        <button
          type="button"
          className="secondary news-reopen"
          onClick={() => updateHome({ newsOpen: true })}
        >
          › Afficher l’actualité
        </button>
      )}

      <div className={`home-layout-v2${newsOpen ? '' : ' news-collapsed'}`}>
        {newsOpen && <NewsSidebar onClose={() => updateHome({ newsOpen: false })} />}

        <div className="home-center">
          <HeatmapPanel />

          <p className="muted">
            Plus fortes variations de la séance du {formatDate(movers.data?.date)} (actions &gt; 1
            $, volume &gt; 200 k, hors splits).
          </p>
          <Status loading={movers.loading} error={movers.error} />
          {movers.data && (
            <div className="grid-2">
              <MoversTable title="Top US" movers={movers.data.gainers} />
              <MoversTable title="Flop US" movers={movers.data.losers} />
            </div>
          )}
        </div>

        {isLoaded && !isSignedIn && (
          <aside className="watchlist-panel">
            <h2>Mes actions</h2>
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
    </>
  )
}
