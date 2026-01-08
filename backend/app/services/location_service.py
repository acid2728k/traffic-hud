import logging
import yt_dlp
from typing import Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self):
        self.location_cache: Optional[Dict] = None
    
    def get_location_from_youtube(self, url: str) -> Optional[Dict]:
        """
        Пытается получить информацию о локации из YouTube метаданных.
        Возвращает: {location: str, timezone: str} или None
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Устанавливаем таймаут для запроса
                info = ydl.extract_info(url, download=False)
                
                # Пытаемся получить локацию из разных полей
                location = None
                timezone = None
                
                # Из описания или названия
                title = info.get('title', '')
                description = info.get('description', '')
                uploader = info.get('uploader', '')
                
                logger.info(f"Analyzing YouTube video: title='{title[:100]}'")
                
                # Простой парсинг - ищем упоминания городов
                # Приоритет: более специфичные ключевые слова первыми
                location_keywords = [
                    # Ocean City (приоритет - более специфичные первыми)
                    ('ocean city md', 'Ocean City, MD, USA', 'America/New_York'),
                    ('ocean city, md', 'Ocean City, MD, USA', 'America/New_York'),
                    ('ocean city', 'Ocean City, MD, USA', 'America/New_York'),
                    # Другие города
                    ('moscow', 'Moscow, Russia', 'Europe/Moscow'),
                    ('москва', 'Moscow, Russia', 'Europe/Moscow'),
                    ('spb', 'Saint Petersburg, Russia', 'Europe/Moscow'),
                    ('petersburg', 'Saint Petersburg, Russia', 'Europe/Moscow'),
                    ('new york', 'New York, USA', 'America/New_York'),
                    ('london', 'London, UK', 'Europe/London'),
                    ('tokyo', 'Tokyo, Japan', 'Asia/Tokyo'),
                    ('paris', 'Paris, France', 'Europe/Paris'),
                    ('berlin', 'Berlin, Germany', 'Europe/Berlin'),
                    ('los angeles', 'Los Angeles, USA', 'America/Los_Angeles'),
                    ('chicago', 'Chicago, USA', 'America/Chicago'),
                    ('miami', 'Miami, USA', 'America/New_York'),
                ]
                
                text_to_search = f"{title} {description} {uploader}".lower()
                logger.info(f"Searching for location in text (first 300 chars): {text_to_search[:300]}")
                
                # Улучшенный поиск: сначала ищем более специфичные совпадения
                for keyword, loc, tz in location_keywords:
                    # Проверяем точное вхождение ключевого слова
                    if keyword in text_to_search:
                        location = loc
                        timezone = tz
                        logger.info(f"✓ Found location: {location} (matched keyword: '{keyword}')")
                        logger.info(f"  Full title: {title}")
                        break
                
                # Если не нашли, пробуем более гибкий поиск для Ocean City
                if not location and ('ocean' in text_to_search and 'city' in text_to_search):
                    # Проверяем, есть ли "md" или "maryland" рядом
                    ocean_idx = text_to_search.find('ocean')
                    city_idx = text_to_search.find('city', ocean_idx)
                    if city_idx > ocean_idx and city_idx < ocean_idx + 20:  # "ocean" и "city" близко друг к другу
                        # Проверяем наличие "md" или "maryland" в тексте
                        if ' md' in text_to_search or 'maryland' in text_to_search:
                            location = 'Ocean City, MD, USA'
                            timezone = 'America/New_York'
                            logger.info(f"✓ Found location via flexible search: {location}")
                
                if location:
                    return {
                        'location': location,
                        'timezone': timezone
                    }
                else:
                    logger.warning(f"Could not determine location from YouTube metadata")
        except Exception as e:
            logger.error(f"Error getting location from YouTube: {e}", exc_info=True)
        
        return None
    
    def get_location(self, force_refresh: bool = False) -> Dict:
        """
        Получает информацию о локации трансляции.
        Сначала пытается из YouTube, затем из конфига, затем дефолт.
        """
        # Если не требуется обновление и есть кеш - возвращаем его
        if not force_refresh and self.location_cache:
            logger.debug(f"Returning cached location: {self.location_cache}")
            return self.location_cache
        
        # Пытаемся получить из YouTube
        if settings.video_source_type == 'youtube_url' and settings.youtube_url:
            try:
                logger.info(f"🔍 Attempting to get location from YouTube: {settings.youtube_url}")
                location_info = self.get_location_from_youtube(settings.youtube_url)
                if location_info:
                    self.location_cache = location_info
                    logger.info(f"✅ Location determined from YouTube: {location_info}")
                    return location_info
                else:
                    logger.warning("⚠️ Could not determine location from YouTube metadata")
            except Exception as e:
                # Не критичная ошибка - просто логируем и продолжаем с дефолтными значениями
                logger.warning(f"⚠️ Failed to get location from YouTube (will use default): {str(e)[:100]}")
                # Не логируем полный traceback для таймаутов - это нормально
        
        # Используем настройки из конфига или дефолт
        location = getattr(settings, 'stream_location', None)
        timezone = getattr(settings, 'stream_timezone', None)
        
        if not location:
            # Если не указано в конфиге, используем дефолт
            location = 'New York, USA'
            timezone = 'America/New_York'
        elif not timezone:
            # Если есть location но нет timezone, пытаемся определить
            timezone = 'UTC'
        
        result = {
            'location': location,
            'timezone': timezone
        }
        
        self.location_cache = result
        logger.info(f"Using location from config/default: {result}")
        return result


location_service = LocationService()
