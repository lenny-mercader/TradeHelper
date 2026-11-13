import { useCallback, useState } from 'react'

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? { ...fallback, ...(JSON.parse(raw) as Partial<T>) } : fallback
  } catch {
    return fallback // private mode, blocked storage, corrupt value...
  }
}

/** Object state remembered in this browser (localStorage). Works, unsaved, when storage is unavailable. */
export function useStoredState<T extends object>(key: string, fallback: T) {
  const [state, setState] = useState<{ key: string; value: T }>(() => ({
    key,
    value: read(key, fallback),
  }))
  // A different key (e.g. another signed-in user) reloads its own saved value.
  const value = state.key === key ? state.value : read(key, fallback)

  const update = useCallback(
    (patch: Partial<T>) => {
      setState((prev) => {
        const base = prev.key === key ? prev.value : read(key, fallback)
        const next = { ...base, ...patch }
        try {
          localStorage.setItem(key, JSON.stringify(next))
        } catch {
          // storage unavailable: keep the in-memory value only
        }
        return { key, value: next }
      })
    },
    // `fallback` is a constant default; `key` decides what is read and written.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key],
  )
  return [value, update] as const
}
