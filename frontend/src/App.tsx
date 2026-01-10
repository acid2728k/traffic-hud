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

  // Debug: Log when component mounts
  useEffect(() => {
    console.log('App component mounted')
    console.log('Current status:', status)
    console.log('Stats:', stats)
    console.log('Stream info:', streamInfo)
  }, [status, stats, streamInfo])

  // Video stream update - moved to top level
  const updateVideoStream = useCallback(() => {
    const img = videoImgRef.current
    if (img && !videoError) {
      // Add timestamp to bypass cache and force reload
      const timestamp = Date.now()
      img.src = `/api/video-stream?t=${timestamp}`
      // Force reload if image fails to update
      img.onerror = () => {
        console.warn('Video frame failed to load, retrying...')
        setTimeout(() => {
          if (img && !videoError) {
            img.src = `/api/video-stream?t=${Date.now()}`
          }
        }, 100)
      }
    }
  }, [videoError])

  const loadData = useCallback(async () => {
    try {
      setStatus('loading')
      const [statsData, leftData, rightData] = await Promise.all([
        api.getStats(),
        api.getEvents('left', 50),
        api.getEvents('right', 50)
      ])
      console.log('Loaded data:', { 
        stats: statsData, 
        leftEvents: leftData.length, 
        rightEvents: rightData.length 
      })
      setStats(statsData)
      setLeftEvents(leftData)
      setRightEvents(rightData)
      setStatus('live')
    } catch (error) {
      console.error('Error loading data:', error)
      setStatus('error')
    }
  }, [])

  const clearLeftEvents = useCallback(() => {
    setLeftEvents([])
    console.log('Left events cleared')
  }, [])

  const clearRightEvents = useCallback(() => {
    setRightEvents([])
    console.log('Right events cleared')
  }, [])

  // Initial data load
  useEffect(() => {
    loadData()
    // Also reload after a short delay to ensure data is fresh
    const timeout = setTimeout(() => {
      loadData()
    }, 2000)
    return () => clearTimeout(timeout)
  }, [loadData])

  // Load location information
  useEffect(() => {
    const loadStreamInfo = async () => {
      try {
        const info = await api.getStreamInfo()
        // Extract city name from location (e.g., "Ocean City, MD, USA" -> "Ocean City")
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
    // Update location every 30 seconds
    const streamInfoInterval = setInterval(loadStreamInfo, 30000)
    return () => clearInterval(streamInfoInterval)
  }, [])

  // Polling fallback for data reload - also refresh data periodically
  useEffect(() => {
    const pollingInterval = setInterval(() => {
      setStatus(currentStatus => {
        if (currentStatus === 'error' || currentStatus === 'loading') {
          loadData()
        } else {
          // Refresh data every 30 seconds to get latest events
          loadData()
        }
        return currentStatus
      })
    }, 30000) // Refresh every 30 seconds
    return () => clearInterval(pollingInterval)
  }, [loadData])

  // WebSocket connection
  useEffect(() => {
    wsService.connect()
    const unsubscribe = wsService.subscribe((message) => {
      if (message.type === 'event_created') {
        const event = message.payload as TrafficEvent
        console.log('WebSocket event received:', { side: event.side, id: event.id })
        if (event.side === 'left') {
          setLeftEvents(prev => {
            // Check if event already exists to avoid duplicates
            const exists = prev.some(e => e.id === event.id)
            if (exists) return prev
            const updated = [event, ...prev].slice(0, 50)
            console.log('Updated left events:', updated.length)
            return updated
          })
        } else if (event.side === 'right') {
          setRightEvents(prev => {
            // Check if event already exists to avoid duplicates
            const exists = prev.some(e => e.id === event.id)
            if (exists) return prev
            const updated = [event, ...prev].slice(0, 50)
            console.log('Updated right events:', updated.length)
            return updated
          })
        }
        // Update statistics
        api.getStats().then(setStats).catch(console.error)
      }
    })
    return () => {
      unsubscribe()
      wsService.disconnect()
    }
  }, [])

  // Video stream update
  useEffect(() => {
    if (videoError) return

    const videoInterval = setInterval(updateVideoStream, 100)
    // First load
    updateVideoStream()
    
    return () => clearInterval(videoInterval)
  }, [updateVideoStream, videoError])

  // Always render UI, even if data is loading
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
            onError={() => {
              console.error('Video stream error, switching to YouTube fallback...')
              setVideoError(true)
            }}
            onLoad={() => {
              setVideoError(false)
            }}
          />
        )}
      </div>
      
      {/* UI Overlay - Always visible */}
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
              onClear={clearLeftEvents}
            />
          </div>
          <div className={styles.centerSpace}></div>
          <div className={styles.rightPanel}>
            <SidePanel
              title="AWAY FROM CAMERA"
              count={stats.right.lastHourCount}
              events={rightEvents}
              side="right"
              onClear={clearRightEvents}
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

