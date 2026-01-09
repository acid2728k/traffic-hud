from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import select
from app.models.database import TrafficEvent, get_session
from app.core.config import settings
from app.services.location_service import location_service
import os
import logging
import cv2
import numpy as np
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Returns statistics for the last hour"""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    with get_session() as session:
        # Left side
        left_count = session.exec(
            select(TrafficEvent).where(
                TrafficEvent.side == "left",
                TrafficEvent.ts >= one_hour_ago
            )
        ).all()
        
        # Right side
        right_count = session.exec(
            select(TrafficEvent).where(
                TrafficEvent.side == "right",
                TrafficEvent.ts >= one_hour_ago
            )
        ).all()
        
        return {
            "left": {"lastHourCount": len(left_count)},
            "right": {"lastHourCount": len(right_count)}
        }


@router.get("/events")
async def get_events(
    side: Optional[str] = Query(None, description="left or right"),
    limit: int = Query(50, ge=1, le=100)
):
    """Returns list of events"""
    with get_session() as session:
        query = select(TrafficEvent).order_by(TrafficEvent.ts.desc())
        
        if side:
            if side not in ["left", "right"]:
                raise HTTPException(status_code=400, detail="side must be 'left' or 'right'")
            query = query.where(TrafficEvent.side == side)
        
        events = session.exec(query.limit(limit)).all()
        
        return [
            {
                "id": e.id,
                "ts": e.ts.isoformat(),
                "side": e.side,
                "lane": e.lane,
                "direction": e.direction,
                "vehicle_type": e.vehicle_type,
                "color": e.color,
                "make_model": e.make_model or "Unknown",
                "make_model_conf": e.make_model_conf,
                "snapshot_path": e.snapshot_path,
                "bbox": e.bbox,
                "track_id": e.track_id
            }
            for e in events
        ]


@router.get("/events/{event_id}")
async def get_event(event_id: int):
    """Returns event details"""
    with get_session() as session:
        event = session.get(TrafficEvent, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {
            "id": event.id,
            "ts": event.ts.isoformat(),
            "side": event.side,
            "lane": event.lane,
            "direction": event.direction,
            "vehicle_type": event.vehicle_type,
            "color": event.color,
            "make_model": event.make_model or "Unknown",
            "make_model_conf": event.make_model_conf,
            "snapshot_path": event.snapshot_path,
            "bbox": event.bbox,
            "track_id": event.track_id,
            "source_meta": event.source_meta
        }


@router.get("/snapshots/{filename}")
async def get_snapshot(filename: str):
    """Returns snapshot file"""
    filepath = os.path.join(settings.snapshots_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(filepath)


@router.get("/stream-info")
async def get_stream_info(force_refresh: bool = Query(False, description="Force refresh location from YouTube")):
    """Returns stream location information"""
    # If cache is empty, force refresh
    if not location_service.location_cache:
        force_refresh = True
    location_info = location_service.get_location(force_refresh=force_refresh)
    logger.info(f"Stream info requested (force_refresh={force_refresh}), returning: {location_info}")
    return location_info


@router.get("/weather")
async def get_weather():
    """Returns weather for stream location"""
    location_info = location_service.get_location()
    location = location_info.get('location', 'Unknown Location')
    
    # In MVP we use mock data, later can connect real API (OpenWeatherMap etc.)
    # For real API, add API key to .env
    import random
    conditions = ['Clear', 'Cloudy', 'Rain', 'Snow', 'Fog']
    
    # Generate realistic data based on location (for demo)
    # In production, this will be a request to OpenWeatherMap API
    return {
        "temperature": random.randint(-5, 25),  # Range depends on location
        "condition": random.choice(conditions),
        "humidity": random.randint(40, 90),
        "windSpeed": random.randint(5, 25),
        "location": location
    }


@router.get("/news")
async def get_news():
    """Returns news for stream location"""
    location_info = location_service.get_location()
    location = location_info.get('location', 'Unknown Location')
    
    # Extract city name (e.g., "Ocean City, MD, USA" -> "Ocean City")
    city = location.split(',')[0].strip()
    
    try:
        # Use Google News RSS to get news for the city
        import feedparser
        import urllib.parse
        
        # Build query for Google News RSS
        query = urllib.parse.quote(f"{city} news")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        # Parse RSS
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:10]:  # Take first 10 news items
            title = entry.get('title', '').strip()
            if title:
                news_items.append(title)
        
        if news_items:
            return {
                "news": news_items,
                "location": city
            }
        
        # Fallback: if RSS doesn't work, return mock data
        return {
            "news": [
                f"Local news updates for {city}",
                f"Traffic monitoring active in {city}",
                f"Weather conditions normal in {city}",
                f"Public services operational in {city}"
            ],
            "location": city
        }
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        # Fallback to mock data on error
        return {
            "news": [
                f"News feed loading for {city}",
                f"Traffic monitoring system operational",
                f"All systems normal in {city}"
            ],
            "location": city
        }


@router.get("/video-stream")
async def video_stream():
    """
    Returns a single frame of processed video with detections (JPEG).
    Frontend updates this endpoint every 100ms to create video effect.
    """
    from app.main import current_frame_with_detections
    
    try:
        frame = current_frame_with_detections
        if frame is not None and frame.size > 0:
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                return Response(content=frame_bytes, media_type="image/jpeg")
        
        # If no frame, send status frame with text
        from app.main import ingest, detector, tracker
        status_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Check status
        if ingest is None or not ingest.is_opened():
            status_text = "Connecting to video stream..."
            color = (0, 255, 255)  # Yellow
        elif detector is None:
            status_text = "Loading YOLO model..."
            color = (0, 255, 255)  # Yellow
        else:
            status_text = "Waiting for video frame..."
            color = (0, 255, 0)  # Green
        
        cv2.putText(status_frame, status_text, (50, 220), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(status_frame, "Check backend logs for details", (50, 260), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        ret, buffer = cv2.imencode('.jpg', black_frame)
        if ret:
            frame_bytes = buffer.tobytes()
            return Response(content=frame_bytes, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Error generating frame: {e}")
        # Send error as image
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, f"Error: {str(e)[:30]}", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        ret, buffer = cv2.imencode('.jpg', error_frame)
        if ret:
            frame_bytes = buffer.tobytes()
            return Response(content=frame_bytes, media_type="image/jpeg")
    
    # Fallback
    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    ret, buffer = cv2.imencode('.jpg', black_frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get("/detections")
async def get_current_detections():
    """
    Returns current detections for display in UI.
    """
    from app.main import current_detections
    
    return {
        "detections": [
            {
                "bbox": det.get("bbox", []),
                "class": det.get("class", "unknown"),
                "confidence": det.get("confidence", 0.0),
                "track_id": det.get("track_id", None)
            }
            for det in current_detections
        ],
        "count": len(current_detections)
    }
