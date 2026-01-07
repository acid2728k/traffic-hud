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

# Static files для snapshots
os.makedirs(settings.snapshots_dir, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=settings.snapshots_dir), name="snapshots")

# Routes
app.include_router(router, prefix="/api", tags=["api"])

# WebSocket
app.add_websocket_route("/ws/events", websocket_endpoint)


# Глобальные объекты для обработки видео
ingest = None
detector = None
tracker = None
counter = None
processing_task = None


def on_new_event(event: dict):
    """Callback при новом событии - отправляет через WebSocket"""
    asyncio.create_task(manager.broadcast({
        "type": "event_created",
        "payload": event
    }))


async def process_video_loop():
    """Основной цикл обработки видео"""
    global ingest, detector, tracker, counter
    
    while True:
        try:
            if ingest is None or not ingest.is_opened():
                logger.info("Initializing video ingest...")
                ingest = VideoIngest()
                ingest._open_stream()
                detector = VehicleDetector()
                tracker = SimpleTracker()
                counter = TrafficCounter()
                logger.info("Video ingest initialized")
            
            frame = ingest.read_frame()
            if frame is None:
                logger.warning("Failed to read frame, reinitializing...")
                ingest.release()
                ingest = None
                await asyncio.sleep(2)
                continue
            
            # Детекция
            detections = detector.detect(frame)
            
            # Трекинг
            tracked = tracker.update(detections)
            
            # Подсчет
            events = counter.process_frame(frame, tracked, on_event=on_new_event)
            
            if events:
                logger.info(f"Detected {len(events)} new events")
            
            # Контроль FPS
            await asyncio.sleep(1.0 / settings.fps)
            
        except Exception as e:
            logger.error(f"Error in video processing loop: {e}", exc_info=True)
            if ingest:
                ingest.release()
                ingest = None
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    
    # Запускаем обработку видео в фоне
    global processing_task
    processing_task = asyncio.create_task(process_video_loop())
    logger.info("Video processing task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
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

