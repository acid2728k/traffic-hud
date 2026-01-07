from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import select
from app.models.database import TrafficEvent, get_session
from app.core.config import settings
import os

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Возвращает статистику за последний час"""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    with get_session() as session:
        # Левая сторона
        left_count = session.exec(
            select(TrafficEvent).where(
                TrafficEvent.side == "left",
                TrafficEvent.ts >= one_hour_ago
            )
        ).all()
        
        # Правая сторона
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
    """Возвращает список событий"""
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
    """Возвращает детали события"""
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
    """Возвращает snapshot файл"""
    filepath = os.path.join(settings.snapshots_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(filepath)

