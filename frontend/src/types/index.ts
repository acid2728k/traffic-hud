export interface TrafficEvent {
  id: number
  ts: string
  side: 'left' | 'right'
  lane: number
  direction: string
  vehicle_type: string
  color: string
  make_model: string
  make_model_conf: number | null
  snapshot_path: string | null
  bbox: string | null
  track_id: number
}

export interface Stats {
  left: { lastHourCount: number }
  right: { lastHourCount: number }
}

export interface WebSocketMessage {
  type: 'event_created' | 'error'
  payload: any
}

