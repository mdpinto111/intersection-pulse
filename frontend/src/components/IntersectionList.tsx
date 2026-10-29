import type { IntersectionOverview } from '../types'
import { CongestionBadge } from './CongestionBadge'

interface Props {
  intersections: IntersectionOverview[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export function IntersectionList({ intersections, selectedId, onSelect }: Props) {
  // Most congested first: that's what an operator needs to see.
  const sorted = [...intersections].sort((a, b) => b.congestion_score - a.congestion_score)
  return (
    <ul className="list" aria-label="Intersections">
      {sorted.map((i) => (
        <li key={i.id}>
          <button
            type="button"
            className={`list__item ${i.id === selectedId ? 'list__item--active' : ''}`}
            onClick={() => onSelect(i.id)}
          >
            <span className="list__name">{i.name}</span>
            <span className="list__meta">
              {i.city} · {i.vehicles} veh.
            </span>
            <CongestionBadge level={i.congestion_level} score={i.congestion_score} />
          </button>
        </li>
      ))}
    </ul>
  )
}
