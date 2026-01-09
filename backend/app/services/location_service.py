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
        Attempts to get location information from YouTube metadata.
        Returns: {location: str, timezone: str} or None
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Try to get location from different fields
                location = None
                timezone = None
                
                # From description or title
                title = info.get('title', '')
                description = info.get('description', '')
                uploader = info.get('uploader', '')
                
                logger.info(f"Analyzing YouTube video: title='{title[:100]}'")
                
                # Simple parsing - search for city mentions
                # Priority: more specific keywords first
                location_keywords = [
                    # Ocean City (priority - more specific first)
                    ('ocean city md', 'Ocean City, MD, USA', 'America/New_York'),
                    ('ocean city, md', 'Ocean City, MD, USA', 'America/New_York'),
                    ('ocean city', 'Ocean City, MD, USA', 'America/New_York'),
                    # Other cities
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
                
                # Improved search: first look for more specific matches
                for keyword, loc, tz in location_keywords:
                    # Check exact keyword match
                    if keyword in text_to_search:
                        location = loc
                        timezone = tz
                        logger.info(f"✓ Found location: {location} (matched keyword: '{keyword}')")
                        logger.info(f"  Full title: {title}")
                        break
                
                # If not found, try flexible search for Ocean City
                if not location and ('ocean' in text_to_search and 'city' in text_to_search):
                    # Check if "md" or "maryland" is nearby
                    ocean_idx = text_to_search.find('ocean')
                    city_idx = text_to_search.find('city', ocean_idx)
                    if city_idx > ocean_idx and city_idx < ocean_idx + 20:  # "ocean" and "city" are close to each other
                        # Check for "md" or "maryland" in text
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
        Gets stream location information.
        First tries from YouTube, then from config, then default.
        """
        # If no refresh required and cache exists - return it
        if not force_refresh and self.location_cache:
            logger.debug(f"Returning cached location: {self.location_cache}")
            return self.location_cache
        
        # Try to get from YouTube
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
                # Not critical error - just log and continue with default values
                logger.warning(f"⚠️ Failed to get location from YouTube (will use default): {str(e)[:100]}")
                # Don't log full traceback for timeouts - this is normal
        
        # Use settings from config or default
        location = getattr(settings, 'stream_location', None)
        timezone = getattr(settings, 'stream_timezone', None)
        
        if not location:
            # If not specified in config, use default
            location = 'New York, USA'
            timezone = 'America/New_York'
        elif not timezone:
            # If location exists but no timezone, try to determine
            timezone = 'UTC'
        
        result = {
            'location': location,
            'timezone': timezone
        }
        
        self.location_cache = result
        logger.info(f"Using location from config/default: {result}")
        return result


location_service = LocationService()
