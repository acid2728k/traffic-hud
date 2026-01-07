import React from 'react'
import { TrafficEvent } from '../types'
import styles from './EventModal.module.css'

interface EventModalProps {
  event: TrafficEvent
  onClose: () => void
}

export const EventModal: React.FC<EventModalProps> = ({ event, onClose }) => {
  const formatTime = (ts: string) => {
    const date = new Date(ts)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  const getSnapshotUrl = (path: string | null) => {
    if (!path) return null
    if (path.startsWith('http')) return path
    return path.startsWith('/') ? path : `/${path}`
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.title}>EVENT DETAILS</div>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        <div className={styles.content}>
          {event.snapshot_path && (
            <div className={styles.snapshotContainer}>
              <img
                src={getSnapshotUrl(event.snapshot_path) || ''}
                alt="Vehicle snapshot"
                className={styles.snapshot}
              />
            </div>
          )}
          <div className={styles.table}>
            <div className={styles.row}>
              <div className={styles.label}>Time:</div>
              <div className={styles.value}>{formatTime(event.ts)}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Side:</div>
              <div className={styles.value}>{event.side.toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Lane:</div>
              <div className={styles.value}>{event.lane}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Direction:</div>
              <div className={styles.value}>{event.direction.replace('_', ' ').toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Vehicle Type:</div>
              <div className={styles.value}>{event.vehicle_type.toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Color:</div>
              <div className={styles.value}>{event.color.toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Make/Model:</div>
              <div className={styles.value}>
                {event.make_model || 'Unknown'}
                {event.make_model_conf !== null && event.make_model_conf > 0 && (
                  <span className={styles.confidence}>
                    {' '}({Math.round(event.make_model_conf * 100)}%)
                  </span>
                )}
              </div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Track ID:</div>
              <div className={styles.value}>{event.track_id}</div>
            </div>
            {event.bbox && (
              <div className={styles.row}>
                <div className={styles.label}>BBox:</div>
                <div className={styles.value}>{event.bbox}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

