import { useAuth, useClerk } from '@clerk/react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { api } from '../api'
import { PriceChart } from '../components/PriceChart'
import { Status } from '../components/Status'
import { formatDate, formatEur, formatLocal, formatPercent, formatVolume, trendClass } from '../format'
import { useApi } from '../hooks/useApi'

export function StockPage() {
  const symbol = (useParams().symbol ?? '').toUpperCase()
  const { isLoaded, isSignedIn, userId } = useAuth()
  const clerk = useClerk()
  // Keyed by user too: `followed` depends on who is signed in. Wait for Clerk to avoid a double load.
  const quote = useApi(isLoaded ? `${symbol}:${userId ?? 'anonymous'}` : null, () =>
    api.instrument(symbol),
  )
  // Wait for the quote: it triggers the first load of the history on the server.
  const history = useApi(quote.data ? symbol : null, () => api.history(symbol))
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  async function toggleFollow() {
    if (!quote.data) return
    if (!isSignedIn) {
      clerk.openSignIn()
      return
    }
    setBusy(true)
    setActionError(null)
    try {
      await (quote.data.followed ? api.unfollow(symbol) : api.follow(symbol))
      quote.reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  const q = quote.data
  return (
    <>
      <Status
        loading={quote.loading}
        error={quote.error}
        loadingText={`Chargement de ${symbol} (première ouverture : quelques secondes)…`}
      />
      {q && (
        <>
          <div className="stock-header">
            <div>
              <h1>
                {q.symbol} <span className="muted">{q.exchange ?? ''}</span>
              </h1>
              <p className="name">{q.name ?? ''}</p>
            </div>
            <div className="actions">
              <button type="button" onClick={toggleFollow} disabled={busy}>
                {q.followed ? 'Ne plus suivre' : 'Suivre'}
              </button>
              <Link className="button secondary" to={`/compare?s=${encodeURIComponent(q.symbol)}`}>
                Comparer
              </Link>
            </div>
          </div>
          {actionError && <p className="error">Erreur : {actionError}</p>}

          <div className="stats">
            <div>
              <span className="muted">Clôture</span>
              <strong>{formatEur(q.close)}</strong>
            </div>
            <div>
              <span className="muted">Variation</span>
              <strong className={trendClass(q.change_percent)}>{formatPercent(q.change_percent)}</strong>
            </div>
            <div>
              <span className="muted">Prix local</span>
              <strong>{formatLocal(q.close_local, q.currency)}</strong>
            </div>
            <div>
              <span className="muted">Volume</span>
              <strong>{formatVolume(q.volume)}</strong>
            </div>
            <div>
              <span className="muted">Séance</span>
              <strong>{formatDate(q.date)}</strong>
            </div>
          </div>

          <Status loading={history.loading} error={history.error} />
          {history.data && <PriceChart history={history.data} />}
        </>
      )}
    </>
  )
}
