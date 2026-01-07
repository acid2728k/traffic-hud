import axios from 'axios'
import { TrafficEvent, Stats } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export const api = {
  getStats: async (): Promise<Stats> => {
    const response = await axios.get(`${API_BASE}/stats`)
    return response.data
  },

  getEvents: async (side?: 'left' | 'right', limit: number = 50): Promise<TrafficEvent[]> => {
    const params = new URLSearchParams()
    if (side) params.append('side', side)
    params.append('limit', limit.toString())
    const response = await axios.get(`${API_BASE}/events?${params}`)
    return response.data
  },

  getEvent: async (eventId: number): Promise<TrafficEvent> => {
    const response = await axios.get(`${API_BASE}/events/${eventId}`)
    return response.data
  },
}

