import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SimpleTracker:
    """
    Simplified tracker based on IoU (Intersection over Union).
    Sufficient for MVP. Can be replaced with ByteTrack/DeepSORT later.
    """
    def __init__(self, max_disappeared: int = 5, iou_threshold: float = 0.3):
        self.next_id = 1
        self.tracks: Dict[int, Dict] = {}  # track_id -> {bbox, class, last_seen_frame}
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold
        self.frame_count = 0
    
    def _iou(self, box1: List[int], box2: List[int]) -> float:
        """Calculates IoU between two bboxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        inter_area = (x2_i - x1_i) * (y2_i - y1_i)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _centroid(self, bbox: List[int]) -> tuple:
        """Calculates bbox center"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Updates tracks based on new detections.
        Returns detections with added track_id.
        """
        self.frame_count += 1
        
        # Remove old tracks
        tracks_to_remove = []
        for track_id, track in self.tracks.items():
            if self.frame_count - track["last_seen_frame"] > self.max_disappeared:
                tracks_to_remove.append(track_id)
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
        
        # If no detections, return empty list
        if not detections:
            return []
        
        # IoU matrix between existing tracks and new detections
        matched = set()
        updated_detections = []
        
        for detection in detections:
            bbox = detection["bbox"]
            best_iou = 0.0
            best_track_id = None
            
            for track_id, track in self.tracks.items():
                if track_id in matched:
                    continue
                iou = self._iou(bbox, track["bbox"])
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                detection["track_id"] = best_track_id
                self.tracks[best_track_id] = {
                    "bbox": bbox,
                    "class": detection["class"],
                    "last_seen_frame": self.frame_count
                }
                matched.add(best_track_id)
            else:
                # Create new track
                track_id = self.next_id
                self.next_id += 1
                detection["track_id"] = track_id
                self.tracks[track_id] = {
                    "bbox": bbox,
                    "class": detection["class"],
                    "last_seen_frame": self.frame_count
                }
            
            updated_detections.append(detection)
        
        return updated_detections

