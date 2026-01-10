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
    // Ensure path starts with /snapshots/ for proper routing
    if (path.startsWith('/snapshots/')) return path
    if (path.startsWith('snapshots/')) return `/${path}`
    return `/snapshots/${path.split('/').pop()}`
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.title}>EVENT DETAILS</div>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        <div className={styles.content}>
          {event.snapshot_path ? (
            <div className={styles.snapshotContainer}>
              <img
                src={getSnapshotUrl(event.snapshot_path) || ''}
                alt="Vehicle snapshot"
                className={styles.snapshot}
                onError={(e) => {
                  console.error('Failed to load snapshot:', event.snapshot_path, getSnapshotUrl(event.snapshot_path))
                  const target = e.target as HTMLImageElement
                  target.style.display = 'none'
                  // Show placeholder if image fails to load
                  const container = target.parentElement
                  if (container) {
                    const placeholder = document.createElement('div')
                    placeholder.textContent = 'Photo not available'
                    placeholder.style.cssText = 'padding: 20px; text-align: center; color: #00ff00;'
                    container.appendChild(placeholder)
                  }
                }}
                onLoad={() => {
                  console.log('Snapshot loaded successfully:', event.snapshot_path)
                }}
              />
            </div>
          ) : (
            <div className={styles.snapshotContainer}>
              <div style={{ padding: '20px', textAlign: 'center', color: '#00ff00' }}>
                Vehicle snapshot not available
              </div>
            </div>
          )}
          
          {/* License Plate Section */}
          <div className={styles.plateSection}>
            <div className={styles.plateLabel}>License Plate:</div>
            <div className={styles.plateContainer}>
              {event.plate_snapshot_path ? (
                <img
                  src={getSnapshotUrl(event.plate_snapshot_path) || ''}
                  alt="License plate"
                  className={styles.plateImage}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
              ) : (
                <div className={styles.plateImagePlaceholder}>No plate image</div>
              )}
              <div className={styles.plateNumber}>
                {event.plate_number || 'XXXXX'}
              </div>
            </div>
          </div>
          
          <div className={styles.table}>
            <div className={styles.row}>
              <div className={styles.label}>Date & Time:</div>
              <div className={styles.value}>{formatTime(event.ts)}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Side:</div>
              <div className={styles.value}>{event.side.toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Brand:</div>
              <div className={styles.value}>
                {event.make_model ? event.make_model.split(' - ')[0] : 'Unknown'}
              </div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Body Type:</div>
              <div className={styles.value}>
                {event.make_model ? (event.make_model.split(' - ')[1] || 'Vehicle') : 'Vehicle'}
              </div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>Color:</div>
              <div className={styles.value}>{event.color.toUpperCase()}</div>
            </div>
            <div className={styles.row}>
              <div className={styles.label}>ID:</div>
              <div className={styles.value}>{event.track_id}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

