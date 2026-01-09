import axios from 'axios'
import { TrafficEvent, Stats } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// Настройка таймаутов для axios
axios.defaults.timeout = 10000 // 10 секунд
axios.defaults.headers.common['Content-Type'] = 'application/json'

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

  getStreamInfo: async (): Promise<{ location: string; timezone: string }> => {
    const response = await axios.get(`${API_BASE}/stream-info`)
    return response.data
  },

  getWeather: async (): Promise<{ temperature: number; condition: string; humidity: number; windSpeed: number; location: string }> => {
    const response = await axios.get(`${API_BASE}/weather`)
    return response.data
  },

  getNews: async (): Promise<{ news: string[]; location: string }> => {
    const response = await axios.get(`${API_BASE}/news`)
    return response.data
  },
}

