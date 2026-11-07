import { useEffect, useState } from 'react'
import { fetchHistory, fetchQuotes, type HistoryPoint, type Quote } from './api'
import { PriceChart } from './components/PriceChart'
import { QuotesTable } from './components/QuotesTable'
import { formatDate } from './format'

const errorMessage = (err: unknown) => (err instanceof Error ? err.message : String(err))

function App() {
  const [quotes, setQuotes] = useState<Quote[] | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [history, setHistory] = useState<{ symbol: string; points: HistoryPoint[] } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchQuotes()
      .then((data) => {
        setQuotes(data)
        setSelected(data[0]?.symbol ?? null)
      })
      .catch((err: unknown) => setError(errorMessage(err)))
  }, [])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    fetchHistory(selected)
      .then((points) => !cancelled && setHistory({ symbol: selected, points }))
      .catch((err: unknown) => !cancelled && setError(errorMessage(err)))
    return () => {
      cancelled = true
    }
  }, [selected])

  const lastUpdate = quotes?.length ? quotes.map((q) => q.date).sort().at(-1) : undefined

  return (
    <main>
      <header>
        <h1>TradeHelper</h1>
        {lastUpdate && <p className="muted">Données de clôture du {formatDate(lastUpdate)}</p>}
      </header>

      {error && <p className="error">Erreur : {error}</p>}
      {!error && quotes === null && <p className="muted">Chargement…</p>}
      {quotes?.length === 0 && (
        <p className="muted">Aucune donnée pour l'instant : la première mise à jour n'a pas encore tourné.</p>
      )}

      {quotes && quotes.length > 0 && (
        <>
          <QuotesTable quotes={quotes} selected={selected} onSelect={setSelected} />
          {history && history.symbol === selected && (
            <PriceChart symbol={history.symbol} history={history.points} />
          )}
        </>
      )}
    </main>
  )
}

export default App
