import { useState } from 'react'
import { api } from './api'
import { IntersectionList } from './components/IntersectionList'
import { NetworkMap } from './components/NetworkMap'
import { StatsPanel } from './components/StatsPanel'
import { VolumeChart } from './components/VolumeChart'
import { usePolling } from './hooks/usePolling'

const REFRESH_MS = 5000
const WINDOWS = [5, 15, 60] as const

export default function App() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [minutes, setMinutes] = useState<number>(15)

  const overview = usePolling((s) => api.overview(minutes, s), REFRESH_MS, [minutes])
  const intersections = overview.data ?? []
  const activeId = selectedId ?? intersections[0]?.id ?? null
  const active = intersections.find((i) => i.id === activeId)

  const stats = usePolling(
    (s) => (activeId ? api.stats(activeId, minutes, s) : Promise.resolve(null)),
    REFRESH_MS,
    [activeId, minutes],
  )
  const series = usePolling(
    (s) => (activeId ? api.timeseries(activeId, 60, 1, s) : Promise.resolve(null)),
    REFRESH_MS,
    [activeId],
  )

  return (
    <div className="layout">
      <header className="header">
        <h1>Intersection Pulse</h1>
        <div className="window-picker" role="group" aria-label="Time window">
          {WINDOWS.map((w) => (
            <button
              key={w}
              type="button"
              className={w === minutes ? 'active' : ''}
              onClick={() => setMinutes(w)}
            >
              {w} min
            </button>
          ))}
        </div>
      </header>

      {overview.error && (
        <div className="error" role="alert">
          Cannot reach the API ({overview.error.message}). Retrying…
        </div>
      )}

      <aside className="sidebar">
        <IntersectionList
          intersections={intersections}
          selectedId={activeId}
          onSelect={setSelectedId}
        />
      </aside>

      <main className="main">
        <NetworkMap intersections={intersections} selectedId={activeId} onSelect={setSelectedId} />

        {active && (
          <div className="card">
            <h2>
              {active.name} <span className="muted">· {active.city}</span>
            </h2>
            {stats.data && <StatsPanel stats={stats.data} />}
            <h3>Last hour, per minute</h3>
            <VolumeChart points={series.data?.points ?? []} />
          </div>
        )}
      </main>
    </div>
  )
}
