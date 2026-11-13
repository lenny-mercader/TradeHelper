/**
 * Squarified treemap layout (Bruls, Huizing, van Wijk 1999): lays out items in nested rows so
 * each tile's area is proportional to its `value`, while keeping tiles close to square (never a
 * sliver 1px wide), which is what makes a treemap readable at a glance.
 *
 * Coordinates are in the same unit as the input `rect` (we pass percentages, 0–100, so the
 * result is pure CSS left/top/width/height with no pixel math: it stays correct at any size).
 */

export type Rect = { x: number; y: number; w: number; h: number }

function worstAspectRatio(values: number[], length: number): number {
  if (values.length === 0) return Infinity
  const sum = values.reduce((a, b) => a + b, 0)
  if (sum <= 0) return Infinity
  const max = Math.max(...values)
  const min = Math.min(...values)
  const s2 = sum * sum
  const l2 = length * length
  return Math.max((l2 * max) / s2, s2 / (l2 * min))
}

function layoutRow<T extends { value: number }>(
  row: T[],
  rect: Rect,
  rowArea: number,
): { tiles: (T & Rect)[]; rest: Rect } {
  const horizontal = rect.w >= rect.h
  const length = horizontal ? rect.h : rect.w
  const thickness = length > 0 ? rowArea / length : 0
  let offset = 0
  const tiles: (T & Rect)[] = row.map((item) => {
    const size = thickness > 0 ? item.value / thickness : 0
    const tile = horizontal
      ? { ...item, x: rect.x, y: rect.y + offset, w: thickness, h: size }
      : { ...item, x: rect.x + offset, y: rect.y, w: size, h: thickness }
    offset += size
    return tile
  })
  const rest: Rect = horizontal
    ? { x: rect.x + thickness, y: rect.y, w: Math.max(rect.w - thickness, 0), h: rect.h }
    : { x: rect.x, y: rect.y + thickness, w: rect.w, h: Math.max(rect.h - thickness, 0) }
  return { tiles, rest }
}

/** `items` should already be sorted by `value` descending (the algorithm assumes it). */
export function squarify<T extends { value: number }>(items: T[], rect: Rect): (T & Rect)[] {
  const totalValue = items.reduce((a, b) => a + b.value, 0)
  if (totalValue <= 0 || items.length === 0 || rect.w <= 0 || rect.h <= 0) return []

  const scale = (rect.w * rect.h) / totalValue
  const scaled = items.map((it) => ({ ...it, value: it.value * scale }))

  const result: (T & Rect)[] = []
  let current = rect
  let remaining = scaled
  let row: typeof scaled = []

  const flush = () => {
    if (row.length === 0) return
    const rowArea = row.reduce((a, b) => a + b.value, 0)
    const { tiles, rest } = layoutRow(row, current, rowArea)
    result.push(...tiles)
    current = rest
    row = []
  }

  while (remaining.length > 0) {
    if (current.w <= 1e-6 || current.h <= 1e-6) break // floating-point sliver left: stop cleanly
    const length = Math.min(current.w, current.h)
    const candidateRow = [...row, remaining[0]]
    const better =
      row.length === 0 ||
      worstAspectRatio(
        row.map((r) => r.value),
        length,
      ) >=
        worstAspectRatio(
          candidateRow.map((r) => r.value),
          length,
        )
    if (better) {
      row = candidateRow
      remaining = remaining.slice(1)
    } else {
      flush()
    }
  }
  flush()
  return result
}
