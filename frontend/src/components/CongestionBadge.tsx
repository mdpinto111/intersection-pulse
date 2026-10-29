import type { CongestionLevel } from '../types'

const LABELS: Record<CongestionLevel, string> = {
  low: 'Fluid',
  moderate: 'Moderate',
  high: 'Congested',
}

export function CongestionBadge({ level, score }: { level: CongestionLevel; score?: number }) {
  return (
    <span className={`badge badge--${level}`} title={score !== undefined ? `score ${score}` : undefined}>
      {LABELS[level]}
    </span>
  )
}
