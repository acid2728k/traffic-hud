from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Session, create_engine, select
from app.core.config import settings


class TrafficEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    side: str  # "left" or "right"
    lane: int  # 1, 2, or 3
    direction: str  # "toward_camera" or "away_from_camera"
    vehicle_type: str  # "car", "truck", "bus", "motorcycle"
    color: str
    make_model: Optional[str] = None
    make_model_conf: Optional[float] = None
    snapshot_path: Optional[str] = None
    plate_number: Optional[str] = None  # Recognized license plate number
    plate_snapshot_path: Optional[str] = None  # Path to plate region snapshot
    bbox: Optional[str] = None  # JSON string: [x1, y1, x2, y2]
    track_id: int
    source_meta: Optional[str] = None  # JSON string for additional metadata


engine = create_engine(settings.database_url, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)

