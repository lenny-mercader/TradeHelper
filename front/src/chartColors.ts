/**
 * Categorical palette for multi-series charts: 8 validated slots (CSS variables --series-1..8,
 * light and dark steps in index.css). Colors follow the entity, never its rank: a symbol keeps
 * its slot while it stays selected, and slots are only handed out when free.
 */
export const SERIES_SLOTS = 8

export const seriesColor = (slot: number) => `var(--series-${slot + 1})`

/** Slot for `symbol`: its previous one if still free, otherwise the first free slot. */
export function assignSlot(
  symbol: string,
  slots: Record<string, number>,
  selected: string[],
): number | null {
  const used = new Set(selected.filter((s) => s !== symbol).map((s) => slots[s]))
  const previous = slots[symbol]
  if (previous !== undefined && !used.has(previous)) return previous
  for (let slot = 0; slot < SERIES_SLOTS; slot++) if (!used.has(slot)) return slot
  return null
}
