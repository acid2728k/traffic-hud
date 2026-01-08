import React from 'react'
import styles from './Header.module.css'

export const Header: React.FC = () => {
  return (
    <div className={styles.header}>
      <div className={styles.title}>TRAFFIC HUD <span className={styles.version}>v. 0.01</span></div>
    </div>
  )
}

