import type { Approach, IntersectionStats } from '../types'
import { CongestionBadge } from './CongestionBadge'

const APPROACH_LABELS: Record<Approach, string> = {
  N: 'North',
  S: 'South',
  E: 'East',
  W: 'West',
}

export function StatsPanel({ stats }: { stats: IntersectionStats }) {
  return (
    <section aria-label="Intersection statistics">
      <div className="kpis">
        <div className="kpi">
          <span className="kpi__label">Vehicles ({stats.window_minutes} min)</span>
          <span className="kpi__value">{stats.total_vehicles.toLocaleString()}</span>
        </div>
        <div className="kpi">
          <span className="kpi__label">Avg speed</span>
          <span className="kpi__value">{stats.avg_speed_kmh} km/h</span>
        </div>
        <div className="kpi">
          <span className="kpi__label">Status</span>
          <span className="kpi__value">
            <CongestionBadge level={stats.congestion_level} score={stats.congestion_score} />
          </span>
        </div>
      </div>

      {stats.approaches.length === 0 ? (
        <p className="muted">No readings in this window yet.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Approach</th>
              <th>Vehicles</th>
              <th>Pedestrians</th>
              <th>Avg speed</th>
              <th>Max queue</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {stats.approaches.map((a) => (
              <tr key={a.approach}>
                <td>{APPROACH_LABELS[a.approach]}</td>
                <td>{a.vehicles}</td>
                <td>{a.pedestrians}</td>
                <td>{a.avg_speed_kmh} km/h</td>
                <td>{a.max_queue_m} m</td>
                <td>
                  <CongestionBadge level={a.congestion_level} score={a.congestion_score} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
