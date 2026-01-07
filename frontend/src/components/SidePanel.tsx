import React, { useState } from 'react'
import { TrafficEvent } from '../types'
import styles from './SidePanel.module.css'
import { EventModal } from './EventModal'

interface SidePanelProps {
  title: string
  count: number
  events: TrafficEvent[]
  side: 'left' | 'right'
}

export const SidePanel: React.FC<SidePanelProps> = ({ title, count, events, side }) => {
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null)

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
          <div className={styles.title}>{title}</div>
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

