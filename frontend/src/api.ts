import type { IntersectionOverview, IntersectionStats, Timeseries } from './types'

const BASE = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { signal })
  if (!response.ok) {
    throw new ApiError(response.status, `GET ${path} failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  overview: (minutes: number, signal?: AbortSignal) =>
    get<IntersectionOverview[]>(`/intersections/overview/?minutes=${minutes}`, signal),

  stats: (id: number, minutes: number, signal?: AbortSignal) =>
    get<IntersectionStats>(`/intersections/${id}/stats/?minutes=${minutes}`, signal),

  timeseries: (id: number, minutes: number, bucket: number, signal?: AbortSignal) =>
    get<Timeseries>(`/intersections/${id}/timeseries/?minutes=${minutes}&bucket=${bucket}`, signal),
}
