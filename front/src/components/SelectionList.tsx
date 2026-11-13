import type { Quote } from '../api'

type Props = {
  quotes: Quote[]
  selected: string[]
  max: number
  colorOf: (symbol: string) => string
  onToggle: (symbol: string) => void
}

/** Checkable list of instruments; doubles as the chart legend (color swatch + name). */
export function SelectionList({ quotes, selected, max, colorOf, onToggle }: Props) {
  const full = selected.length >= max
  return (
    <div className="selection-list">
      <div className="selection-head">
        <strong>Actions</strong>
        <span className="muted">
          {selected.length}/{max}
          {full && ` · ${max} maximum`}
        </span>
      </div>
      <ul>
        {quotes.map((q) => {
          const checked = selected.includes(q.symbol)
          const disabled = !checked && full
          return (
            <li key={q.symbol} className={disabled ? 'disabled' : undefined}>
              <label title={disabled ? `${max} actions maximum` : undefined}>
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => onToggle(q.symbol)}
                />
                <span
                  className="swatch"
                  style={{ background: checked ? colorOf(q.symbol) : 'transparent' }}
                />
                <span className="symbol">{q.symbol}</span>
                <span className="name muted">{q.name ?? ''}</span>
              </label>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
