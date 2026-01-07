import React from 'react'
import styles from './StatusBar.module.css'

interface StatusBarProps {
  status: 'live' | 'error' | 'loading'
  onRetry?: () => void
}

export const StatusBar: React.FC<StatusBarProps> = ({ status, onRetry }) => {
  return (
    <div className={styles.statusBar}>
      <div className={styles.title}>TRAFFIC HUD</div>
      <div className={styles.status}>
        <span className={`${styles.statusIndicator} ${styles[status]}`}>
          {status === 'live' && '● STREAM: LIVE'}
          {status === 'error' && '● STREAM: ERROR'}
          {status === 'loading' && '● STREAM: CONNECTING...'}
        </span>
        {status === 'error' && onRetry && (
          <button className={styles.retryButton} onClick={onRetry}>
            RETRY
          </button>
        )}
      </div>
    </div>
  )
}

