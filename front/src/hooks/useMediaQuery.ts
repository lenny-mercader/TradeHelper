import { useSyncExternalStore } from 'react'

/** Live-updates on resize (not just on mount), e.g. useMediaQuery('(max-width: 767px)'). */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches,
    () => false, // SSR snapshot; unused here but required by the hook's signature
  )
}
