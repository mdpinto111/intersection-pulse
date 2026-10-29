export type CongestionLevel = 'low' | 'moderate' | 'high'
export type Approach = 'N' | 'S' | 'E' | 'W'

export interface IntersectionOverview {
  id: number
  name: string
  city: string
  latitude: string
  longitude: string
  is_active: boolean
  vehicles: number
  avg_speed_kmh: number
  congestion_score: number
  congestion_level: CongestionLevel
}

export interface ApproachStats {
  approach: Approach
  vehicles: number
  pedestrians: number
  avg_speed_kmh: number
  max_queue_m: number
  samples: number
  congestion_score: number
  congestion_level: CongestionLevel
}

export interface IntersectionStats {
  intersection_id: number
  window_minutes: number
  total_vehicles: number
  avg_speed_kmh: number
  congestion_score: number
  congestion_level: CongestionLevel
  approaches: ApproachStats[]
}

export interface TimeseriesPoint {
  bucket_start: string
  vehicles: number
  avg_speed_kmh: number
}

export interface Timeseries {
  intersection_id: number
  minutes: number
  bucket: number
  points: TimeseriesPoint[]
}
