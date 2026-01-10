import json
import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import logging
from app.core.config import settings
from app.models.database import TrafficEvent, get_session
from app.utils.plate_blur import blur_plate_region
from app.utils.color_classifier import classify_color
from app.utils.make_model_classifier import classify_make_model

logger = logging.getLogger(__name__)


class TrafficCounter:
    def __init__(self):
        self.roi_config = self._load_roi_config()
        self.counted_tracks: Dict[int, str] = {}  # track_id -> side where it was counted ("left" or "right")
        self.track_history: Dict[int, List[Tuple[float, float]]] = {}  # track_id -> list of (x, y) centroids
        
    def _load_roi_config(self) -> Dict:
        """Loads ROI configuration from JSON"""
        config_path = settings.roi_config_path
        if not os.path.exists(config_path):
            logger.warning(f"ROI config not found: {config_path}, using defaults")
            return self._default_config()
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _default_config(self) -> Dict:
        """Returns default configuration"""
        return {
            "left_side": {
                "name": "LEFT SIDE (TOWARD CAMERA)",
                "direction": "toward_camera",
                "roi": {"polygon": [[0, 0], [640, 0], [640, 480], [0, 480]]},
                "counting_line": {"start": [100, 240], "end": [540, 240], "direction": "toward_camera"},
                "lanes": [
                    {"id": 1, "polygon": [[0, 0], [213, 0], [213, 480], [0, 480]]},
                    {"id": 2, "polygon": [[213, 0], [427, 0], [427, 480], [213, 480]]},
                    {"id": 3, "polygon": [[427, 0], [640, 0], [640, 480], [427, 480]]}
                ]
            },
            "right_side": {
                "name": "RIGHT SIDE (AWAY FROM CAMERA)",
                "direction": "away_from_camera",
                "roi": {"polygon": [[0, 0], [640, 0], [640, 480], [0, 480]]},
                "counting_line": {"start": [100, 240], "end": [540, 240], "direction": "away_from_camera"},
                "lanes": [
                    {"id": 1, "polygon": [[0, 0], [213, 0], [213, 480], [0, 480]]},
                    {"id": 2, "polygon": [[213, 0], [427, 0], [427, 480], [213, 480]]},
                    {"id": 3, "polygon": [[427, 0], [640, 0], [640, 480], [427, 480]]}
                ]
            }
        }
    
    def _point_in_polygon(self, point: Tuple[float, float], polygon: List[List[int]]) -> bool:
        """Checks if point is inside polygon"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _line_intersection(self, line1: Tuple[Tuple[float, float], Tuple[float, float]], 
                          line2: Tuple[Tuple[float, float], Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        """Checks intersection of two line segments"""
        (x1, y1), (x2, y2) = line1
        (x3, y3), (x4, y4) = line2
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)
        return None
    
    def _get_lane(self, centroid: Tuple[float, float], side: str) -> int:
        """Determines lane by centroid"""
        side_config = self.roi_config[f"{side}_side"]
        for lane in side_config["lanes"]:
            if self._point_in_polygon(centroid, lane["polygon"]):
                return lane["id"]
        return 1  # Default
    
    def _crossed_counting_line(self, track_id: int, side: str) -> bool:
        """Checks if track crossed counting line"""
        if track_id not in self.track_history or len(self.track_history[track_id]) < 2:
            return False
        
        side_config = self.roi_config[f"{side}_side"]
        line_start = side_config["counting_line"]["start"]
        line_end = side_config["counting_line"]["end"]
        direction = side_config["counting_line"]["direction"]
        
        history = self.track_history[track_id]
        
        # Check intersection between consecutive points
        for i in range(len(history) - 1):
            p1 = history[i]
            p2 = history[i + 1]
            
            intersection = self._line_intersection(
                (p1, p2),
                ((line_start[0], line_start[1]), (line_end[0], line_end[1]))
            )
            
            if intersection:
                # Check direction
                dy = p2[1] - p1[1]
                if direction == "toward_camera":
                    # Movement toward camera: y should decrease (moving up)
                    if dy < 0:
                        logger.debug(f"Track {track_id} crossed {side} counting line (toward_camera, dy={dy:.1f})")
                        return True
                else:  # away_from_camera
                    # Movement away from camera: y should increase (moving down)
                    if dy > 0:
                        logger.debug(f"Track {track_id} crossed {side} counting line (away_from_camera, dy={dy:.1f})")
                        return True
        
        return False
    
    def process_frame(self, frame: np.ndarray, detections: List[Dict], 
                     on_event: Optional[Callable[[Dict], None]] = None) -> List[Dict]:
        """
        Processes frame with detections and creates passage events.
        on_event: callback(event_dict) called on new event
        """
        events = []
        
        for det in detections:
            track_id = det["track_id"]
            bbox = det["bbox"]
            vehicle_type = det["class"]
            
            # Calculate centroid
            x1, y1, x2, y2 = bbox
            centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Update track history
            if track_id not in self.track_history:
                self.track_history[track_id] = []
            self.track_history[track_id].append(centroid)
            # Limit history
            if len(self.track_history[track_id]) > 10:
                self.track_history[track_id] = self.track_history[track_id][-10:]
            
            # Determine side based primarily on X position (left vs right half of screen)
            frame_width = frame.shape[1] if len(frame.shape) > 1 else 1920
            
            # Simple rule: left half = left side, right half = right side
            side = "left" if centroid[0] < frame_width / 2 else "right"
            
            # Log for debugging (only for first few tracks to avoid spam)
            if track_id <= 5 or track_id % 50 == 0:
                logger.info(f"Track {track_id}: centroid=({centroid[0]:.1f}, {centroid[1]:.1f}), frame_width={frame_width}, assigned_side={side}")
            
            # Optional: Validate with ROI if centroid is outside expected ROI
            # This helps catch edge cases but doesn't override the main rule
            side_config = self.roi_config[f"{side}_side"]
            roi_polygon = side_config["roi"]["polygon"]
            in_expected_roi = self._point_in_polygon(centroid, roi_polygon)
            
            if not in_expected_roi:
                # Check if centroid is in the other side's ROI
                other_side = "right" if side == "left" else "left"
                other_side_config = self.roi_config[f"{other_side}_side"]
                other_roi_polygon = other_side_config["roi"]["polygon"]
                if self._point_in_polygon(centroid, other_roi_polygon):
                    # Centroid is in other side's ROI - switch sides
                    side = other_side
                    logger.info(f"Track {track_id}: Switched to {side} (centroid in {other_side} ROI but X position suggested {('right' if side == 'left' else 'left')})")
            
            if side is None:
                continue
            
            # Check if vehicle should be counted
            # Only count if not already counted, or if counted on different side (shouldn't happen, but safety check)
            already_counted_side = self.counted_tracks.get(track_id)
            if already_counted_side is None or already_counted_side != side:
                side_config = self.roi_config[f"{side}_side"]
                
                # Check if vehicle is in ROI
                in_roi = self._point_in_polygon(centroid, side_config["roi"]["polygon"])
                
                if in_roi:
                    # Count immediately when vehicle is detected in ROI
                    # This creates events as soon as vehicles are detected and tracked by machine vision
                    # We require at least 2 points in history to ensure it's a real track (not a false detection)
                    history_len = len(self.track_history.get(track_id, []))
                    
                    # Create event immediately when vehicle is in ROI and has been tracked for at least 2 frames
                    # This ensures we catch vehicles as soon as they're detected, not waiting for line crossing
                    should_count = history_len >= 2
                    
                    if should_count:
                        self.counted_tracks[track_id] = side
                        logger.info(f"Track {track_id} counted on {side} side immediately after detection (centroid=({centroid[0]:.1f}, {centroid[1]:.1f}), in_roi={in_roi}, history_len={history_len})")
                    
                    # Determine lane
                    lane = self._get_lane(centroid, side)
                    
                    # Classify color
                    color = classify_color(frame, tuple(bbox))
                    
                    # Classify make/model
                    try:
                        make_model, make_model_conf = classify_make_model(frame, tuple(bbox))
                        if make_model:
                            logger.debug(f"Classified vehicle {track_id} as {make_model} (confidence: {make_model_conf:.2f})")
                    except Exception as e:
                        logger.warning(f"Error classifying make/model for track {track_id}: {e}")
                        make_model, make_model_conf = None, 0.0
                    
                    # Create snapshot for both sides (not just left)
                    snapshot_path = self._save_snapshot(frame, bbox, track_id)
                    
                    # Create event
                    event = {
                        "ts": datetime.utcnow(),
                        "side": side,
                        "lane": lane,
                        "direction": self.roi_config[f"{side}_side"]["direction"],
                        "vehicle_type": vehicle_type,
                        "color": color,
                        "make_model": make_model if make_model else "Unknown",
                        "make_model_conf": make_model_conf,
                        "snapshot_path": snapshot_path,
                        "bbox": json.dumps(bbox),
                        "track_id": track_id,
                        "source_meta": json.dumps({"confidence": det.get("confidence", 0.0)})
                    }
                    
                    # Save to database
                    self._save_event(event)
                    
                    events.append(event)
                    
                    # Callback is called in main.py after process_frame
                    # (removed from here for proper async handling)
        
        return events
    
    def _save_snapshot(self, frame: np.ndarray, bbox: List[int], track_id: int) -> str:
        """Saves snapshot with license plate blurring"""
        x1, y1, x2, y2 = bbox
        # Add small padding
        padding = 10
        h, w = frame.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        snapshot = frame[y1:y2, x1:x2].copy()
        
        # Blur license plate
        snapshot = blur_plate_region(snapshot, (0, 0, x2 - x1, y2 - y1))
        
        # Save
        os.makedirs(settings.snapshots_dir, exist_ok=True)
        filename = f"snapshot_{track_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        filepath = os.path.join(settings.snapshots_dir, filename)
        cv2.imwrite(filepath, snapshot)
        
        return f"/snapshots/{filename}"
    
    def _save_event(self, event: Dict):
        """Saves event to database"""
        try:
            with get_session() as session:
                db_event = TrafficEvent(**event)
                session.add(db_event)
                session.commit()
        except Exception as e:
            logger.error(f"Error saving event: {e}")

