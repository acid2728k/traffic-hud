import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import styles from './NewsTicker.module.css'

interface NewsTickerProps {
  location?: string // Kept for compatibility, but not used (backend determines location itself)
}

export const NewsTicker: React.FC<NewsTickerProps> = () => {
  const [news, setNews] = useState<string[]>([])

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const data = await api.getNews()
        setNews(data.news || [])
      } catch (error) {
        console.error('Error fetching news:', error)
        setNews([`News feed unavailable`])
      }
    }

    fetchNews()
    // Update every 10 minutes
    const interval = setInterval(fetchNews, 10 * 60 * 1000)
    return () => clearInterval(interval)
  }, []) // Removed location from dependencies, as backend determines location itself

  if (news.length === 0) {
    return null
  }

  const newsText = news.join(' • ')

  return (
    <div className={styles.tickerContainer}>
      <div className={styles.label}>NEWS:</div>
      <div className={styles.ticker}>
        <div className={styles.tickerContent}>
          {newsText} • {newsText}
        </div>
      </div>
    </div>
  )
}

