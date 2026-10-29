import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet'
import type { CongestionLevel, IntersectionOverview } from '../types'

const COLORS: Record<CongestionLevel, string> = {
  low: '#16a34a',
  moderate: '#f59e0b',
  high: '#dc2626',
}

function FlyTo({ target }: { target: IntersectionOverview | undefined }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyTo([Number(target.latitude), Number(target.longitude)], 15, { duration: 0.8 })
  }, [map, target])
  return null
}

interface Props {
  intersections: IntersectionOverview[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export function NetworkMap({ intersections, selectedId, onSelect }: Props) {
  const selected = intersections.find((i) => i.id === selectedId)
  return (
    <MapContainer center={[32.08, 34.78]} zoom={13} className="map" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyTo target={selected} />
      {intersections.map((i) => (
        <CircleMarker
          key={i.id}
          center={[Number(i.latitude), Number(i.longitude)]}
          radius={i.id === selectedId ? 14 : 10}
          pathOptions={{
            color: '#0f172a',
            weight: i.id === selectedId ? 3 : 1,
            fillColor: COLORS[i.congestion_level],
            fillOpacity: 0.85,
          }}
          eventHandlers={{ click: () => onSelect(i.id) }}
        >
          <Tooltip>
            <strong>{i.name}</strong>
            <br />
            {i.vehicles} vehicles · {i.avg_speed_kmh} km/h
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
