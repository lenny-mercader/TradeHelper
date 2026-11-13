import { useMemo } from 'react'
import { Link } from 'react-router'
import { api } from '../api'
import { formatEur, formatPercent, formatVolume } from '../format'
import { useApi } from '../hooks/useApi'
import { squarify } from '../treemap'
import { Status } from './Status'

// Fixed, theme-independent colors: a heatmap is its own self-contained visual zone (like a
// market-data terminal), not themed chrome — white tile labels must stay legible either way.
const UP = '#0ca30c'
const DOWN = '#d03b3b'
const NEUTRAL = '#33333c'
// Daily moves beyond this magnitude saturate to the full color; most daily moves are smaller.
const MAX_INTENSITY_PERCENT = 5

function hexToRgb(hex: string): [number, number, number] {
  const n = Number.parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function mix(a: string, b: string, t: number): string {
  const [ar, ag, ab] = hexToRgb(a)
  const [br, bg, bb] = hexToRgb(b)
  const lerp = (x: number, y: number) => Math.round(x + (y - x) * t)
  return `rgb(${lerp(ar, br)}, ${lerp(ag, bg)}, ${lerp(ab, bb)})`
}

function tileColor(changePercent: number): string {
  const t = Math.min(Math.abs(changePercent) / MAX_INTENSITY_PERCENT, 1)
  return mix(NEUTRAL, changePercent >= 0 ? UP : DOWN, t)
}

type Props = {
  limit?: number
}

/** Top US stocks by dollar volume (our free proxy for size, see the back), one tile each. */
export function HeatmapPanel({ limit = 100 }: Props) {
  const heat = useApi(`heatmap:${limit}`, () => api.heatmap(limit))

  const tiles = useMemo(() => {
    if (!heat.data) return []
    const items = heat.data.tiles.map((t) => ({ ...t, value: t.dollar_volume }))
    return squarify(items, { x: 0, y: 0, w: 100, h: 100 })
  }, [heat.data])

  return (
    <section className="panel heatmap-panel">
      <h2>Heatmap — Top 100 US (volume)</h2>
      <Status loading={heat.loading} error={heat.error} />
      {tiles.length > 0 && (
        <div className="heatmap-grid">
          {tiles.map((tile) => (
            <Link
              key={tile.symbol}
              to={`/stock/${encodeURIComponent(tile.symbol)}`}
              className="heatmap-tile"
              style={{
                left: `${tile.x}%`,
                top: `${tile.y}%`,
                width: `${tile.w}%`,
                height: `${tile.h}%`,
                background: tileColor(tile.change_percent),
              }}
              title={`${tile.symbol} — ${tile.name ?? ''}\n${formatPercent(tile.change_percent)} · ${formatEur(tile.close)} · ${formatVolume(tile.volume)}`}
            >
              <span className="heatmap-symbol">{tile.symbol}</span>
              <span className="heatmap-change">{formatPercent(tile.change_percent)}</span>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}
