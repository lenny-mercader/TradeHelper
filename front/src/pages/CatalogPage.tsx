import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { api, type CatalogSort } from '../api'
import { Status } from '../components/Status'
import { CONTINENTS } from '../countryGroups'
import { formatCompactLocal, formatEur, formatPercent, trendClass } from '../format'
import { useApi } from '../hooks/useApi'

const SORTS: { value: CatalogSort; label: string }[] = [
  { value: 'market_cap', label: 'Capitalisation' },
  { value: 'change', label: 'Variation' },
  { value: 'name', label: 'Nom' },
]

function useFilters() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const countries = params.getAll('country')
  const sector = params.get('sector') ?? ''
  const sort = (params.get('sort') as CatalogSort) || 'market_cap'
  const order: 'asc' | 'desc' = params.get('order') === 'asc' ? 'asc' : 'desc'
  const page = Math.max(1, Number(params.get('page')) || 1)

  function update(patch: {
    q?: string
    countries?: string[]
    sector?: string
    sort?: CatalogSort
    order?: 'asc' | 'desc'
    page?: number
  }) {
    const next = new URLSearchParams()
    const nq = patch.q ?? q
    const ncountries = patch.countries ?? countries
    const nsector = patch.sector ?? sector
    if (nq) next.set('q', nq)
    for (const c of ncountries) next.append('country', c)
    if (nsector) next.set('sector', nsector)
    next.set('sort', patch.sort ?? sort)
    next.set('order', patch.order ?? order)
    // Any filter/sort change goes back to page 1, except an explicit page change.
    const samePage = patch.page !== undefined
    next.set('page', String(samePage ? patch.page : 1))
    setParams(next)
  }

  return { q, countries, sector, sort, order, page, update }
}

const SEARCH_DEBOUNCE_MS = 300

export function CatalogPage() {
  const { q, countries, sector, sort, order, page, update } = useFilters()
  // Debounced locally: the URL (and the refetch it triggers) only updates after a short pause,
  // not on every keystroke.
  const [searchInput, setSearchInput] = useState(q)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== q) update({ q: searchInput })
    }, SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput])

  const facets = useApi('catalog-facets', api.catalogFacets)
  const key = `catalog:${q}:${countries.join(',')}:${sector}:${sort}:${order}:${page}`
  const result = useApi(key, () => api.catalog({ q, countries, sector, sort, order, page }))

  // Each continent only lists the countries actually present in the data; continents with none
  // of their countries present are skipped entirely.
  const continents = useMemo(() => {
    const present = new Set(facets.data?.countries ?? [])
    return CONTINENTS.map((c) => ({ ...c, countries: c.countries.filter((n) => present.has(n)) })).filter(
      (c) => c.countries.length > 0,
    )
  }, [facets.data])
  const groupedCountries = useMemo(() => new Set(continents.flatMap((c) => c.countries)), [continents])
  const ungroupedCountries = useMemo(
    () => (facets.data?.countries ?? []).filter((c) => !groupedCountries.has(c)),
    [facets.data, groupedCountries],
  )

  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  function toggleExpanded(name: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }
      return next
    })
  }

  function toggleCountry(country: string) {
    update({
      countries: countries.includes(country)
        ? countries.filter((c) => c !== country)
        : [...countries, country],
    })
  }

  function toggleContinent(continentCountries: string[]) {
    const allChecked = continentCountries.every((c) => countries.includes(c))
    update({
      countries: allChecked
        ? countries.filter((c) => !continentCountries.includes(c))
        : [...new Set([...countries, ...continentCountries])],
    })
  }

  const pageCount = result.data ? Math.ceil(result.data.total / result.data.page_size) : 0

  return (
    <>
      <h1>Catalogue des actions</h1>
      <p className="muted">
        Tout le catalogue américain (capitalisation/secteur se complètent progressivement), plus
        les actions internationales déjà consultées.
      </p>

      <div className="catalog-layout">
        <aside className="catalog-filters panel">
          <div className="search">
            <input
              type="search"
              placeholder="Nom ou symbole…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>

          <h3>Pays</h3>
          <ul className="catalog-country-list">
            {continents.map((cont) => {
              const allChecked = cont.countries.every((c) => countries.includes(c))
              const isExpanded = expanded.has(cont.name)
              return (
                <li key={cont.name} className="catalog-continent">
                  <div className="catalog-continent-row">
                    <label>
                      <input
                        type="checkbox"
                        checked={allChecked}
                        onChange={() => toggleContinent(cont.countries)}
                      />
                      {cont.name}
                    </label>
                    <button
                      type="button"
                      className="catalog-continent-toggle"
                      aria-label={isExpanded ? `Replier ${cont.name}` : `Déplier ${cont.name}`}
                      aria-expanded={isExpanded}
                      onClick={() => toggleExpanded(cont.name)}
                    >
                      {isExpanded ? '▾' : '▸'}
                    </button>
                  </div>
                  {isExpanded && (
                    <ul className="catalog-continent-countries">
                      {cont.countries.map((c) => (
                        <li key={c}>
                          <label>
                            <input
                              type="checkbox"
                              checked={countries.includes(c)}
                              onChange={() => toggleCountry(c)}
                            />
                            {c}
                          </label>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              )
            })}
            {ungroupedCountries.map((c) => (
              <li key={c}>
                <label>
                  <input
                    type="checkbox"
                    checked={countries.includes(c)}
                    onChange={() => toggleCountry(c)}
                  />
                  {c}
                </label>
              </li>
            ))}
          </ul>

          <h3>Secteur</h3>
          <select value={sector} onChange={(e) => update({ sector: e.target.value })}>
            <option value="">Tous les secteurs</option>
            {facets.data?.sectors.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </aside>

        <div className="catalog-main">
          <div className="toolbar">
            <div className="segmented" role="group" aria-label="Trier par">
              {SORTS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  aria-pressed={sort === s.value}
                  onClick={() => update({ sort: s.value })}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="secondary"
              onClick={() => update({ order: order === 'desc' ? 'asc' : 'desc' })}
            >
              {order === 'desc' ? '↓ Décroissant' : '↑ Croissant'}
            </button>
            {result.data && <span className="muted">{result.data.total} résultats</span>}
          </div>

          <Status loading={result.loading} error={result.error} />

          {result.data && result.data.rows.length === 0 && (
            <p className="muted">Aucune action ne correspond à ces filtres.</p>
          )}

          {result.data && result.data.rows.length > 0 && (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Symbole</th>
                    <th>Nom</th>
                    <th>Pays</th>
                    <th>Secteur</th>
                    <th>Clôture (EUR)</th>
                    <th>Variation</th>
                    <th>Capitalisation (EUR)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.rows.map((r) => (
                    <tr key={r.symbol}>
                      <td className="symbol">
                        <Link to={`/stock/${encodeURIComponent(r.symbol)}`}>{r.symbol}</Link>
                      </td>
                      <td className="name">{r.name ?? ''}</td>
                      <td className="muted">{r.country ?? '—'}</td>
                      <td className="muted">{r.sector ?? '—'}</td>
                      <td>{formatEur(r.close)}</td>
                      <td className={trendClass(r.change_percent)}>
                        {formatPercent(r.change_percent)}
                      </td>
                      <td className="muted">{formatCompactLocal(r.market_cap, 'EUR')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {pageCount > 1 && (
            <div className="pagination">
              <button type="button" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>
                ‹ Précédent
              </button>
              <span className="muted">
                Page {page} / {pageCount}
              </span>
              <button
                type="button"
                disabled={page >= pageCount}
                onClick={() => update({ page: page + 1 })}
              >
                Suivant ›
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
