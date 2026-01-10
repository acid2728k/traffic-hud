import React, { useState, useEffect } from 'react'
import { TrafficEvent } from '../types'
import styles from './SidePanel.module.css'
import { EventModal } from './EventModal'

interface UnifiedSidePanelProps {
  leftCount: number
  rightCount: number
  leftEvents: TrafficEvent[]
  rightEvents: TrafficEvent[]
  onClearLeft?: () => void
  onClearRight?: () => void
}

export const UnifiedSidePanel: React.FC<UnifiedSidePanelProps> = ({
  leftCount,
  rightCount,
  leftEvents,
  rightEvents,
  onClearLeft,
  onClearRight
}) => {
  const [activeTab, setActiveTab] = useState<'left' | 'right'>('left')
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null)

  // Debug logging
  useEffect(() => {
    console.log(`UnifiedSidePanel:`, { 
      activeTab, 
      leftCount, 
      rightCount, 
      leftEventsCount: leftEvents.length, 
      rightEventsCount: rightEvents.length 
    })
  }, [activeTab, leftCount, rightCount, leftEvents, rightEvents])

  const formatTime = (ts: string) => {
    const date = new Date(ts)
    return date.toLocaleTimeString('en-US', { hour12: false })
  }

  const getSnapshotUrl = (path: string | null) => {
    if (!path) return null
    if (path.startsWith('http')) return path
    return path.startsWith('/') ? path : `/${path}`
  }

  const currentEvents = activeTab === 'left' ? leftEvents : rightEvents
  const currentCount = activeTab === 'left' ? leftCount : rightCount
  const currentTitle = activeTab === 'left' ? 'TOWARD CAMERA' : 'AWAY FROM CAMERA'
  const handleClear = activeTab === 'left' ? onClearLeft : onClearRight

  return (
    <>
      <div className={styles.panel}>
        {/* Tabs */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'left' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('left')}
          >
            <span className={styles.tabTitle}>TOWARD</span>
            <span className={styles.tabCount}>{leftCount}</span>
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'right' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('right')}
          >
            <span className={styles.tabTitle}>AWAY</span>
            <span className={styles.tabCount}>{rightCount}</span>
          </button>
        </div>

        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <div className={styles.title}>{currentTitle}</div>
            {currentEvents.length > 0 && handleClear && (
              <button 
                className={styles.clearButton}
                onClick={handleClear}
                title="Clear events list"
              >
                CLEAR
              </button>
            )}
          </div>
          <div className={styles.count}>Last 60 min: {currentCount}</div>
        </div>

        {/* Events List */}
        <div className={styles.list}>
          {currentEvents.length === 0 ? (
            <div className={styles.empty}>No events yet</div>
          ) : (
            currentEvents.map((event) => (
              <div
                key={event.id}
                className={styles.eventItem}
                onClick={() => setSelectedEvent(event)}
              >
                {event.snapshot_path && (
                  <img
                    src={getSnapshotUrl(event.snapshot_path) || ''}
                    alt="Vehicle"
                    className={styles.thumbnail}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                )}
                <div className={styles.eventInfo}>
                  <div className={styles.eventTime}>{formatTime(event.ts)}</div>
                  <div className={styles.eventDetails}>
                    Lane {event.lane} • {event.vehicle_type} • {event.color}
                    {event.make_model && event.make_model !== 'Unknown' && (
                      <> • {event.make_model}</>
                    )}
                  </div>
                  {event.plate_number && (
                    <div className={styles.plateNumber}>
                      {event.plate_number}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      {selectedEvent && (
        <EventModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </>
  )
}

// Keep old SidePanel for backward compatibility if needed
interface SidePanelProps {
  title: string
  count: number
  events: TrafficEvent[]
  side: 'left' | 'right'
  onClear?: () => void
}

export const SidePanel: React.FC<SidePanelProps> = ({ title, count, events, side, onClear }) => {
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null)

  useEffect(() => {
    console.log(`SidePanel ${side}:`, { title, count, eventsCount: events.length, events })
  }, [title, count, events, side])

  const handleClear = () => {
    if (onClear) {
      onClear()
    }
  }

  const formatTime = (ts: string) => {
    const date = new Date(ts)
    return date.toLocaleTimeString('en-US', { hour12: false })
  }

  const getSnapshotUrl = (path: string | null) => {
    if (!path) return null
    if (path.startsWith('http')) return path
    return path.startsWith('/') ? path : `/${path}`
  }

  return (
    <>
      <div className={styles.panel}>
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <div className={styles.title}>{title}</div>
            {events.length > 0 && onClear && (
              <button 
                className={styles.clearButton}
                onClick={handleClear}
                title="Clear events list"
              >
                CLEAR
              </button>
            )}
          </div>
          <div className={styles.count}>Last 60 min: {count}</div>
        </div>
        <div className={styles.list}>
          {events.length === 0 ? (
            <div className={styles.empty}>No events yet</div>
          ) : (
            events.map((event) => (
              <div
                key={event.id}
                className={styles.eventItem}
                onClick={() => setSelectedEvent(event)}
              >
                {side === 'left' && event.snapshot_path && (
                  <img
                    src={getSnapshotUrl(event.snapshot_path) || ''}
                    alt="Vehicle"
                    className={styles.thumbnail}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                )}
                <div className={styles.eventInfo}>
                  <div className={styles.eventTime}>{formatTime(event.ts)}</div>
                  <div className={styles.eventDetails}>
                    Lane {event.lane} • {event.vehicle_type} • {event.color}
                    {event.make_model && event.make_model !== 'Unknown' && (
                      <> • {event.make_model}</>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      {selectedEvent && (
        <EventModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </>
  )
}

