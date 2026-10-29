import { render, screen, within } from '@testing-library/react'
import type { IntersectionStats } from '../types'
import { StatsPanel } from './StatsPanel'

const stats: IntersectionStats = {
  intersection_id: 1,
  window_minutes: 15,
  total_vehicles: 1234,
  avg_speed_kmh: 31.5,
  congestion_score: 0.7,
  congestion_level: 'high',
  approaches: [
    {
      approach: 'N',
      vehicles: 800,
      pedestrians: 40,
      avg_speed_kmh: 22,
      max_queue_m: 95,
      samples: 90,
      congestion_score: 0.8,
      congestion_level: 'high',
    },
    {
      approach: 'E',
      vehicles: 434,
      pedestrians: 12,
      avg_speed_kmh: 44,
      max_queue_m: 8,
      samples: 90,
      congestion_score: 0.1,
      congestion_level: 'low',
    },
  ],
}

describe('StatsPanel', () => {
  it('shows the KPIs', () => {
    render(<StatsPanel stats={stats} />)
    expect(screen.getByText('1,234')).toBeInTheDocument()
    expect(screen.getByText('31.5 km/h')).toBeInTheDocument()
  })

  it('renders one row per approach with its congestion level', () => {
    render(<StatsPanel stats={stats} />)
    const rows = screen.getAllByRole('row').slice(1) // skip header
    expect(rows).toHaveLength(2)
    expect(within(rows[0]).getByText('North')).toBeInTheDocument()
    expect(within(rows[0]).getByText('Congested')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Fluid')).toBeInTheDocument()
  })

  it('shows an empty state when there is no reading', () => {
    render(<StatsPanel stats={{ ...stats, approaches: [] }} />)
    expect(screen.getByText(/no readings/i)).toBeInTheDocument()
  })
})
