import React from 'react'
import { StreamInfo } from './StreamInfo'
import { Weather } from './Weather'
import { NewsTicker } from './NewsTicker'
import styles from './StatusBar.module.css'

interface StatusBarProps {
  status: 'live' | 'error' | 'loading'
  onRetry?: () => void
  location?: string // Оставлено для совместимости, но не используется
}

export const StatusBar: React.FC<StatusBarProps> = ({ status, onRetry }) => {
  return (
    <div className={styles.statusBar}>
      <div className={styles.leftSection}>
        <StreamInfo />
        <Weather />
      </div>
      <div className={styles.centerSection}>
        <NewsTicker />
      </div>
      <div className={styles.rightSection}>
        <div className={styles.liveBadge}>● LIVE</div>
        {status === 'error' && onRetry && (
          <button className={styles.retryButton} onClick={onRetry}>
            RETRY
          </button>
        )}
      </div>
    </div>
  )
}

