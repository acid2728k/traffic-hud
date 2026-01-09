from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from app.api.routes import router
from app.api.websocket import websocket_endpoint, manager
from app.models.database import init_db
from app.services.ingest import VideoIngest
from app.services.detection import VehicleDetector
from app.services.tracking import SimpleTracker
from app.services.counting import TrafficCounter
from app.core.config import settings
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Traffic HUD API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for snapshots
os.makedirs(settings.snapshots_dir, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=settings.snapshots_dir), name="snapshots")

# Routes
app.include_router(router, prefix="/api", tags=["api"])

# WebSocket
app.add_websocket_route("/ws/events", websocket_endpoint)


# Global objects for video processing
ingest = None
detector = None
tracker = None
counter = None
processing_task = None

# Global buffer for the last processed frame with detections
current_frame_with_detections = None
current_detections = []


async def on_new_event(event: dict):
    """Callback for new event - broadcasts via WebSocket"""
    try:
        await manager.broadcast({
            "type": "event_created",
            "payload": event
        })
        logger.info(f"Broadcasted event: track_id={event.get('track_id')}, side={event.get('side')}")
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")


async def process_video_loop():
    """Main video processing loop"""
    global ingest, detector, tracker, counter
    
    while True:
        try:
            if ingest is None or not ingest.is_opened():
                logger.info("Initializing video ingest...")
                try:
                    ingest = VideoIngest()
                    ingest._open_stream()
                    if not ingest.is_opened():
                        raise ValueError("Video stream not opened")
                    detector = VehicleDetector()
                    logger.info("YOLO model loaded")
                    tracker = SimpleTracker()
                    counter = TrafficCounter()
                    logger.info("Video ingest initialized successfully")
                except Exception as e:
                    logger.error(f"Error initializing video ingest: {e}", exc_info=True)
                    ingest = None
                    await asyncio.sleep(5)
                    continue
            
            frame = ingest.read_frame()
            if frame is None:
                logger.warning("Failed to read frame, reinitializing...")
                ingest.release()
                ingest = None
                await asyncio.sleep(2)
                continue
            
            # Detection
            detections = detector.detect(frame)
            if detections:
                logger.debug(f"Detected {len(detections)} vehicles in frame")
            
            # Tracking
            tracked = tracker.update(detections)
            if tracked:
                logger.debug(f"Tracking {len(tracked)} vehicles")
            
            # Draw detections on frame for streaming
            from app.utils.video_drawer import draw_detections, draw_counting_lines
            frame_with_detections = draw_detections(frame.copy(), tracked, show_track_id=True, show_confidence=True)
            frame_with_detections = draw_counting_lines(frame_with_detections, counter.roi_config)
            
            # Save frame and detections for streaming
            global current_frame_with_detections, current_detections
            current_frame_with_detections = frame_with_detections
            current_detections = tracked
            
            # Counting
            # Create list of events for async processing
            events = counter.process_frame(frame, tracked, on_event=None)
            
            # Send events via WebSocket asynchronously
            for event in events:
                await on_new_event(event)
            
            if events:
                logger.info(f"Detected {len(events)} new events")
            
            # FPS control
            await asyncio.sleep(1.0 / settings.fps)
            
        except Exception as e:
            logger.error(f"Error in video processing loop: {e}", exc_info=True)
            if ingest:
                ingest.release()
                ingest = None
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    """Initialization on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    
    # Clear location cache on startup to determine location from YouTube
    from app.services.location_service import location_service
    location_service.location_cache = None
    logger.info("Location cache cleared, will be determined from YouTube on first request")
    
    # Start video processing in background
    global processing_task
    processing_task = asyncio.create_task(process_video_loop())
    logger.info("Video processing task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ingest, processing_task
    if ingest:
        ingest.release()
    if processing_task:
        processing_task.cancel()
    logger.info("Application shutdown")


@app.get("/")
async def root():
    return {"status": "ok", "service": "Traffic HUD API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

