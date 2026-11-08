import { Link } from 'react-router'
import { api, type Mover } from '../api'
import { QuoteTable } from '../components/QuoteTable'
import { Status } from '../components/Status'
import { formatDate, formatEur, formatPercent, formatVolume, trendClass } from '../format'
import { useApi } from '../hooks/useApi'

function MoversTable({ title, movers }: { title: string; movers: Mover[] }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {movers.length === 0 ? (
        <p className="muted">Pas encore de données.</p>
      ) : (
        <table className="data compact">
          <tbody>
            {movers.map((m) => (
              <tr key={m.symbol}>
                <td className="symbol">
                  <Link to={`/stock/${encodeURIComponent(m.symbol)}`}>{m.symbol}</Link>
                </td>
                <td className="name">{m.name ?? ''}</td>
                <td>{formatEur(m.close)}</td>
                <td className={trendClass(m.change_percent)}>{formatPercent(m.change_percent)}</td>
                <td className="muted">{formatVolume(m.volume)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export function MarketPage() {
  const movers = useApi('movers', api.movers)
  const watchlist = useApi('watchlist', api.watchlist)

  return (
    <>
      <h1>Marché US</h1>
      <p className="muted">
        Plus fortes variations de la séance du {formatDate(movers.data?.date)} (actions &gt; 1 $,
        volume &gt; 200 k, hors splits).
      </p>
      <Status loading={movers.loading} error={movers.error} />
      {movers.data && (
        <div className="grid-2">
          <MoversTable title="Plus fortes hausses" movers={movers.data.gainers} />
          <MoversTable title="Plus fortes baisses" movers={movers.data.losers} />
        </div>
      )}

      <h2 className="section-title">
        Mes actions suivies <Link to="/watchlist">gérer</Link>
      </h2>
      <Status loading={watchlist.loading} error={watchlist.error} />
      {watchlist.data?.length === 0 && (
        <p className="muted">Aucune action suivie. Cherche une action et clique sur « Suivre ».</p>
      )}
      {watchlist.data && watchlist.data.length > 0 && <QuoteTable quotes={watchlist.data} />}
    </>
  )
}
