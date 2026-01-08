import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import styles from './StreamInfo.module.css'

export const StreamInfo: React.FC = () => {
  const [location, setLocation] = useState<string>('Loading...')
  const [timezone, setTimezone] = useState<string>('UTC')
  const [currentTime, setCurrentTime] = useState<string>('')
  const [currentDate, setCurrentDate] = useState<string>('')

  useEffect(() => {
    // Загружаем информацию о локации с сервера
    const loadStreamInfo = () => {
      api.getStreamInfo()
        .then(info => {
          setLocation(info.location)
          setTimezone(info.timezone)
        })
        .catch(error => {
          console.error('Error loading stream info:', error)
          setLocation('Unknown Location')
          setTimezone('UTC')
        })
    }
    
    loadStreamInfo()
    // Обновляем каждые 30 секунд на случай если YouTube метаданные обновились
    const interval = setInterval(loadStreamInfo, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
      const dateFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
      setCurrentTime(formatter.format(now))
      setCurrentDate(dateFormatter.format(now))
    }

    updateTime()
    const interval = setInterval(updateTime, 1000)

    return () => clearInterval(interval)
  }, [timezone])

  return (
    <div className={styles.streamInfo}>
      <div className={styles.location}>{location}</div>
      <div className={styles.time}>{currentTime}</div>
      <div className={styles.date}>{currentDate}</div>
    </div>
  )
}

