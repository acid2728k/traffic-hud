import { useEffect, useState, useRef, useCallback } from 'react'
import { Header } from './components/Header'
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
  const [streamInfo, setStreamInfo] = useState<{ location: string; timezone: string; city: string } | null>(null)
  const videoImgRef = useRef<HTMLImageElement>(null)
  const [videoError, setVideoError] = useState(false)

  // Обновление видео стрима - вынесено на верхний уровень
  const updateVideoStream = useCallback(() => {
    const img = videoImgRef.current
    if (img && !videoError) {
      // Добавляем timestamp для обхода кеша
      img.src = `/api/video-stream?t=${Date.now()}`
    }
  }, [videoError])

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
    
    // Загружаем информацию о локации
    const loadStreamInfo = async () => {
      try {
        const info = await api.getStreamInfo()
        // Извлекаем название города из локации (например, "Ocean City, MD, USA" -> "Ocean City")
        const city = info.location.split(',')[0].trim()
        setStreamInfo({
          location: info.location,
          timezone: info.timezone,
          city: city
        })
      } catch (error) {
        console.error('Error loading stream info:', error)
        setStreamInfo({
          location: 'Unknown Location',
          timezone: 'UTC',
          city: 'Unknown'
        })
      }
    }
    
    loadStreamInfo()
    // Обновляем локацию каждые 30 секунд
    const streamInfoInterval = setInterval(loadStreamInfo, 30000)

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

    // Обновляем кадр каждые 100ms (~10 FPS) только если нет ошибки
    let videoInterval: NodeJS.Timeout | null = null
    if (!videoError) {
      videoInterval = setInterval(updateVideoStream, 100)
      // Первая загрузка
      updateVideoStream()
    }

    return () => {
      clearInterval(pollingInterval)
      clearInterval(streamInfoInterval)
      if (videoInterval) clearInterval(videoInterval)
      unsubscribe()
      wsService.disconnect()
    }
  }, [updateVideoStream, videoError])

  return (
    <div className={styles.app}>
      {/* Video background with computer vision overlay */}
      <div className={styles.videoContainer}>
        {videoError ? (
          <iframe
            className={styles.video}
            src="https://www.youtube.com/embed/H0Z6faxNLCI?autoplay=1&mute=1&controls=0&loop=1&playlist=H0Z6faxNLCI"
            allow="autoplay; encrypted-media"
            allowFullScreen
          />
        ) : (
          <img
            ref={videoImgRef}
            className={styles.video}
            alt="Traffic stream with detections"
            style={{ objectFit: 'cover' }}
            onError={(e) => {
              console.error('Video stream error, switching to YouTube fallback...')
              setVideoError(true)
            }}
            onLoad={() => {
              setVideoError(false)
            }}
          />
        )}
      </div>
      
      {/* UI Overlay */}
      <div className={styles.overlay}>
        <div className={styles.gridOverlay}></div>
        <div className={styles.topSection}>
          <Header />
          <StatusBar status={status} onRetry={loadData} location={streamInfo?.city || 'Loading...'} />
        </div>
        <div className={styles.content}>
          <div className={styles.leftPanel}>
            <SidePanel
              title="TOWARD CAMERA"
              count={stats.left.lastHourCount}
              events={leftEvents}
              side="left"
            />
          </div>
          <div className={styles.centerSpace}></div>
          <div className={styles.rightPanel}>
            <SidePanel
              title="AWAY FROM CAMERA"
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
    </div>
  )
}

export default App

