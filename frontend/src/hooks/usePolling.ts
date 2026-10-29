import { useEffect, useRef, useState } from 'react'

interface PollingState<T> {
  data: T | null
  error: Error | null
  loading: boolean
}

/**
 * Calls `fetcher` immediately and then every `intervalMs`.
 * In-flight requests are aborted when the dependencies change or the
 * component unmounts, so a slow response can never overwrite newer data.
 */
export function usePolling<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  intervalMs: number,
  deps: unknown[],
): PollingState<T> {
  const [state, setState] = useState<PollingState<T>>({ data: null, error: null, loading: true })
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    let controller = new AbortController()
    setState((s) => ({ ...s, loading: true }))

    const run = async () => {
      controller.abort()
      controller = new AbortController()
      try {
        const data = await fetcherRef.current(controller.signal)
        setState({ data, error: null, loading: false })
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        setState((s) => ({ ...s, error: err as Error, loading: false }))
      }
    }

    run()
    const id = window.setInterval(run, intervalMs)
    return () => {
      window.clearInterval(id)
      controller.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps])

  return state
}
