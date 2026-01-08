from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Video source
    video_source_type: str = "file"  # file, youtube_url, hls_url, rtsp_url
    video_source_url: Optional[str] = None
    video_source_file: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # Processing
    fps: int = 10
    roi_config_path: str = "roi_config.json"
    
    # Storage
    database_url: str = "sqlite:///./traffic_events.db"
    snapshots_dir: str = "./static/snapshots"
    event_ttl_hours: int = 24
    
    # Model
    yolo_model: str = "yolov8n.pt"
    confidence_threshold: float = 0.25
    
    # Stream location (можно переопределить через .env)
    stream_location: str = "New York, USA"
    stream_timezone: str = "America/New_York"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

