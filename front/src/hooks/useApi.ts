import { useCallback, useEffect, useState } from 'react'

type State<T> = { key: string; data?: T; error?: string }

/**
 * Loads `fetcher()` whenever `key` changes. Results of a previous key are never shown
 * for the current one. `reload()` fetches the same key again.
 */
export function useApi<T>(key: string | null, fetcher: () => Promise<T>) {
  const [state, setState] = useState<State<T> | null>(null)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    if (key === null) return
    let cancelled = false
    fetcher()
      .then((data) => !cancelled && setState({ key, data }))
      .catch(
        (err: unknown) =>
          !cancelled &&
          setState({ key, error: err instanceof Error ? err.message : String(err) }),
      )
    return () => {
      cancelled = true
    }
    // `fetcher` is recreated on every render; `key` identifies what it loads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, version])

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  const current = state && state.key === key ? state : null
  return {
    data: current?.data,
    error: current?.error,
    loading: key !== null && current === null,
    reload,
  }
}
