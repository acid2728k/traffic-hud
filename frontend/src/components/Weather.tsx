import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import styles from './Weather.module.css'

interface WeatherData {
  temperature: number
  condition: string
  humidity: number
  windSpeed: number
}

interface WeatherProps {
  location?: string // Оставлено для совместимости, но не используется (backend сам определяет локацию)
}

export const Weather: React.FC<WeatherProps> = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setLoading(true)
        const data = await api.getWeather()
        setWeather({
          temperature: data.temperature,
          condition: data.condition,
          humidity: data.humidity,
          windSpeed: data.windSpeed
        })
        setLoading(false)
      } catch (error) {
        console.error('Error fetching weather:', error)
        setLoading(false)
      }
    }

    fetchWeather()
    // Обновляем каждые 5 минут
    const interval = setInterval(fetchWeather, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, []) // Убрали location из зависимостей, так как backend сам определяет локацию

  if (loading || !weather) {
    return (
      <div className={styles.weather}>
        <div className={styles.loading}>Loading weather...</div>
      </div>
    )
  }

  return (
    <div className={styles.weather}>
      <div className={styles.temperature}>{weather.temperature}°C</div>
      <div className={styles.condition}>{weather.condition}</div>
      <div className={styles.details}>
        <span>H: {weather.humidity}%</span>
        <span>W: {weather.windSpeed} km/h</span>
      </div>
    </div>
  )
}

