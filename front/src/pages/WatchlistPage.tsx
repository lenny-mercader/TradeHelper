import { useAuth } from '@clerk/react'
import { useState } from 'react'
import { Link } from 'react-router'
import { api, type Period, type Quote } from '../api'
import { assignSlot, SERIES_SLOTS, seriesColor } from '../chartColors'
import { PerformanceChart } from '../components/PerformanceChart'
import { QuoteTable } from '../components/QuoteTable'
import { SearchBox } from '../components/SearchBox'
import { SelectionList } from '../components/SelectionList'
import { SignInPrompt } from '../components/SignInPrompt'
import { Status } from '../components/Status'
import { useApi } from '../hooks/useApi'
import { useStoredState } from '../hooks/useStoredState'

const DEFAULT_CHECKED = 3

type ViewState = {
  /** null until the user changes the selection: the first DEFAULT_CHECKED stocks are used. */
  selected: string[] | null
  period: Period
  /** Color slot of each symbol, kept so a stock keeps its color. */
  slots: Record<string, number>
}

// Not persisted on purpose: the page always opens on the list, whatever was last chosen.
const DEFAULT_VIEW: ViewState = { selected: null, period: '1Y', slots: {} }

/** Slots for the current selection: stored ones when still free, otherwise the first free one. */
function resolveSlots(selected: string[], stored: Record<string, number>) {
  const slots: Record<string, number> = { ...stored }
  const placed: string[] = []
  for (const symbol of selected) {
    const slot = assignSlot(symbol, slots, placed)
    if (slot !== null) slots[symbol] = slot
    placed.push(symbol)
  }
  return slots
}

function ChartView({
  quotes,
  state,
  update,
}: {
  quotes: Quote[]
  state: ViewState
  update: (patch: Partial<ViewState>) => void
}) {
  const [panelOpen, setPanelOpen] = useState(false)
  const symbols = quotes.map((q) => q.symbol)
  const selected = (state.selected ?? symbols.slice(0, DEFAULT_CHECKED)).filter((s) =>
    symbols.includes(s),
  )
  const slots = resolveSlots(selected, state.slots)
  const colorOf = (symbol: string) => seriesColor(slots[symbol] ?? 0)

  function toggle(symbol: string) {
    if (selected.includes(symbol)) {
      update({ selected: selected.filter((s) => s !== symbol), slots })
      return
    }
    if (selected.length >= SERIES_SLOTS) return
    const slot = assignSlot(symbol, slots, selected)
    if (slot === null) return
    update({ selected: [...selected, symbol], slots: { ...slots, [symbol]: slot } })
  }

  const list = (
    <SelectionList
      quotes={quotes}
      selected={selected}
      max={SERIES_SLOTS}
      colorOf={colorOf}
      onToggle={toggle}
    />
  )

  return (
    <div className="perf-layout">
      <div className="perf-main">
        <button
          type="button"
          className="secondary panel-toggle"
          aria-label="Choisir les actions affichées"
          aria-expanded={panelOpen}
          onClick={() => setPanelOpen(true)}
        >
          ☰ Actions ({selected.length}/{SERIES_SLOTS})
        </button>
        <PerformanceChart
          symbols={selected}
          period={state.period}
          onPeriodChange={(period) => update({ period })}
          colorOf={colorOf}
        />
      </div>

      {/* Desktop: fixed column on the right. */}
      <aside className="perf-side">{list}</aside>

      {/* Phone: the same list in a panel sliding from the right. */}
      {panelOpen && (
        <div className="drawer-backdrop" onClick={() => setPanelOpen(false)}>
          <aside
            className="drawer"
            role="dialog"
            aria-label="Actions affichées"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="link drawer-close"
              aria-label="Fermer"
              onClick={() => setPanelOpen(false)}
            >
              ✕
            </button>
            {list}
          </aside>
        </div>
      )}
    </div>
  )
}

export function WatchlistPage() {
  const { isLoaded, isSignedIn, userId } = useAuth()
  const watchlist = useApi(isSignedIn ? `watchlist:${userId}` : null, api.watchlist)
  const [viewState, updateView] = useStoredState<ViewState>(
    `tradehelper:watchlist-view:${userId ?? 'anonymous'}`,
    DEFAULT_VIEW,
  )
  // Always starts on "Liste" on every visit; not remembered across page loads.
  const [view, setView] = useState<'list' | 'chart'>('list')
  const [pending, setPending] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  // Shows a toggled favorite instantly instead of waiting for the round trip + refetch.
  const [favoriteOverrides, setFavoriteOverrides] = useState<Record<string, boolean>>({})
  // Fresh data (after any reload) replaces the optimistic guess; adjusted during render
  // (React's recommended pattern), not in an effect, so it lands before the browser paints.
  const [lastWatchlistData, setLastWatchlistData] = useState(watchlist.data)
  if (watchlist.data !== lastWatchlistData) {
    setLastWatchlistData(watchlist.data)
    setFavoriteOverrides({})
  }

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

  async function toggleFavorite(symbol: string, favorite: boolean) {
    setFavoriteOverrides((o) => ({ ...o, [symbol]: favorite }))
    setActionError(null)
    try {
      await (favorite ? api.favorite(symbol) : api.unfavorite(symbol))
      watchlist.reload()
    } catch (err) {
      // Drop the optimistic guess for this symbol and report the real state.
      setFavoriteOverrides((o) => {
        const { [symbol]: _removed, ...rest } = o
        return rest
      })
      setActionError(err instanceof Error ? err.message : String(err))
    }
  }

  if (!isLoaded) return <p className="muted">Chargement…</p>
  if (!isSignedIn) {
    return (
      <>
        <h1>Actions suivies</h1>
        <SignInPrompt />
      </>
    )
  }

  const quotes = (watchlist.data ?? []).map((q) =>
    q.symbol in favoriteOverrides ? { ...q, favorite: favoriteOverrides[q.symbol] } : q,
  )
  const symbols = quotes.map((q) => q.symbol)

  return (
    <>
      <div className="page-head">
        <h1>Actions suivies</h1>
        <div className="segmented" role="group" aria-label="Affichage">
          <button type="button" aria-pressed={view === 'list'} onClick={() => setView('list')}>
            Liste
          </button>
          <button type="button" aria-pressed={view === 'chart'} onClick={() => setView('chart')}>
            Graphique
          </button>
        </div>
      </div>
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

      {quotes.length > 0 && view === 'list' && (
        <QuoteTable
          quotes={quotes}
          onRemove={(symbol) => run(`Retrait de ${symbol}…`, () => api.unfollow(symbol))}
          onToggleFavorite={toggleFavorite}
        />
      )}
      {quotes.length > 0 && view === 'chart' && (
        <ChartView quotes={quotes} state={viewState} update={updateView} />
      )}
    </>
  )
}
