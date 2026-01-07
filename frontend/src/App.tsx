import React, { useEffect, useState } from 'react'
import { StatusBar } from './components/StatusBar'
import { SidePanel } from './components/SidePanel'
import { api } from './services/api'
import { wsService } from './services/websocket'
import { TrafficEvent, Stats } from './types'
import styles from './App.module.css'

function App() {
  const [stats, setStats] = useState<Stats>({ left: { lastHourCount: 0 }, right: { lastHourCount: 0 } })
  const [leftEvents, setLeftEvents] = useState<TrafficEvent[]>([])
  const [rightEvents, setRightEvents] = useState<TrafficEvent[]>([])
  const [status, setStatus] = useState<'live' | 'error' | 'loading'>('loading')

  const loadData = async () => {
    try {
      setStatus('loading')
      const [statsData, leftData, rightData] = await Promise.all([
        api.getStats(),
        api.getEvents('left', 50),
        api.getEvents('right', 50)
      ])
      setStats(statsData)
      setLeftEvents(leftData)
      setRightEvents(rightData)
      setStatus('live')
    } catch (error) {
      console.error('Error loading data:', error)
      setStatus('error')
    }
  }

  useEffect(() => {
    loadData()

    // Polling fallback каждые 5 секунд
    const pollingInterval = setInterval(() => {
      if (status === 'error' || status === 'loading') {
        loadData()
      }
    }, 5000)

    // WebSocket подключение
    wsService.connect()
    const unsubscribe = wsService.subscribe((message) => {
      if (message.type === 'event_created') {
        const event = message.payload as TrafficEvent
        if (event.side === 'left') {
          setLeftEvents(prev => {
            const updated = [event, ...prev].slice(0, 50)
            return updated
          })
        } else {
          setRightEvents(prev => {
            const updated = [event, ...prev].slice(0, 50)
            return updated
          })
        }
        // Обновляем статистику
        api.getStats().then(setStats).catch(console.error)
      }
    })

    return () => {
      clearInterval(pollingInterval)
      unsubscribe()
      wsService.disconnect()
    }
  }, [])

  return (
    <div className={styles.app}>
      <StatusBar status={status} onRetry={loadData} />
      <div className={styles.content}>
        <div className={styles.leftPanel}>
          <SidePanel
            title="LEFT SIDE (TOWARD CAMERA)"
            count={stats.left.lastHourCount}
            events={leftEvents}
            side="left"
          />
        </div>
        <div className={styles.rightPanel}>
          <SidePanel
            title="RIGHT SIDE (AWAY FROM CAMERA)"
            count={stats.right.lastHourCount}
            events={rightEvents}
            side="right"
          />
        </div>
      </div>
      <div className={styles.footer}>
        <div className={styles.accessDenied}>ACCESS DENIED</div>
      </div>
    </div>
  )
}

export default App

