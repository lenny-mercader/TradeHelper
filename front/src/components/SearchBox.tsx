import { useEffect, useState } from 'react'
import { api, type SearchResult } from '../api'

type Props = {
  placeholder?: string
  onSelect: (result: SearchResult) => void
}

const DEBOUNCE_MS = 300

export function SearchBox({ placeholder = 'Rechercher une action (nom ou symbole)…', onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<{ query: string; items: SearchResult[] } | null>(null)
  const [open, setOpen] = useState(false)
  const trimmed = query.trim()

  useEffect(() => {
    if (!trimmed) return
    const controller = new AbortController()
    const timer = setTimeout(() => {
      api
        .search(trimmed, controller.signal)
        .then((items) => setResults({ query: trimmed, items }))
        .catch(() => {
          /* aborted or failed: keep previous results */
        })
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [trimmed])

  const items = trimmed && results ? results.items : []
  const searching = trimmed !== '' && results?.query !== trimmed

  function choose(result: SearchResult) {
    onSelect(result)
    setQuery('')
    setOpen(false)
  }

  return (
    <div className="search">
      <input
        type="search"
        value={query}
        placeholder={placeholder}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && items[0]) choose(items[0])
          if (e.key === 'Escape') setOpen(false)
        }}
      />
      {open && trimmed && (
        <ul className="search-results">
          {searching && items.length === 0 && <li className="muted">Recherche…</li>}
          {!searching && items.length === 0 && <li className="muted">Aucun résultat</li>}
          {items.map((r) => (
            <li key={r.symbol}>
              <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => choose(r)}>
                <span className="symbol">{r.symbol}</span>
                <span className="name">{r.name ?? ''}</span>
                <span className="muted">{r.exchange ?? ''}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
