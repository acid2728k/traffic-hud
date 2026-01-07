import { WebSocketMessage } from '../types'

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private listeners: Set<(message: WebSocketMessage) => void> = new Set()

  connect() {
    const wsUrl = import.meta.env.VITE_WS_URL || 
      (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + 
      '//' + window.location.host + '/ws/events'
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.listeners.forEach(listener => listener(message))
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.ws = null
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      this.attemptReconnect()
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.connect()
      }, this.reconnectDelay)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  subscribe(callback: (message: WebSocketMessage) => void) {
    this.listeners.add(callback)
    return () => {
      this.listeners.delete(callback)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
  }
}

export const wsService = new WebSocketService()

