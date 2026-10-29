import {
  CartesianGrid,
  ComposedChart,
  Bar,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TimeseriesPoint } from '../types'

const formatTime = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export function VolumeChart({ points }: { points: TimeseriesPoint[] }) {
  if (points.length === 0) return <p className="muted">Waiting for data…</p>

  return (
    <div className="chart" role="img" aria-label="Vehicle volume and average speed over time">
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="bucket_start" tickFormatter={formatTime} fontSize={12} />
          <YAxis yAxisId="veh" fontSize={12} />
          <YAxis yAxisId="speed" orientation="right" unit=" km/h" width={64} fontSize={12} />
          <Tooltip labelFormatter={(v) => formatTime(String(v))} />
          <Bar yAxisId="veh" dataKey="vehicles" name="Vehicles" fill="#3b82f6" radius={[3, 3, 0, 0]} />
          <Line
            yAxisId="speed"
            dataKey="avg_speed_kmh"
            name="Avg speed"
            stroke="#0f172a"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
