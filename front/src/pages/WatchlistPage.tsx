import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api'
import { QuoteTable } from '../components/QuoteTable'
import { SearchBox } from '../components/SearchBox'
import { Status } from '../components/Status'
import { useApi } from '../hooks/useApi'

export function WatchlistPage() {
  const watchlist = useApi('watchlist', api.watchlist)
  const [pending, setPending] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function run(label: string, action: () => Promise<unknown>) {
    setPending(label)
    setActionError(null)
    try {
      await action()
      watchlist.reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setPending(null)
    }
  }

  const symbols = watchlist.data?.map((q) => q.symbol) ?? []

  return (
    <>
      <h1>Actions suivies</h1>
      <p className="muted">Mises à jour chaque soir après la clôture américaine.</p>

      <div className="toolbar">
        <SearchBox
          placeholder="Ajouter une action…"
          onSelect={(r) => run(`Ajout de ${r.symbol}…`, () => api.follow(r.symbol))}
        />
        {symbols.length > 1 && (
          <Link className="button" to={`/compare?s=${encodeURIComponent(symbols.slice(0, 10).join(','))}`}>
            Comparer {Math.min(symbols.length, 10)} actions
          </Link>
        )}
      </div>

      {pending && <p className="muted">{pending}</p>}
      {actionError && <p className="error">Erreur : {actionError}</p>}
      <Status loading={watchlist.loading} error={watchlist.error} />
      {watchlist.data?.length === 0 && <p className="muted">Aucune action suivie pour l'instant.</p>}
      {watchlist.data && watchlist.data.length > 0 && (
        <QuoteTable
          quotes={watchlist.data}
          onRemove={(symbol) => run(`Retrait de ${symbol}…`, () => api.unfollow(symbol))}
        />
      )}
    </>
  )
}
