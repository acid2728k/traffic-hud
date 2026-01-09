import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SimpleTracker:
    """
    Improved tracker based on IoU with motion prediction.
    Uses velocity estimation for better track association.
    """
    def __init__(self, max_disappeared: int = 10, iou_threshold: float = 0.3, distance_threshold: float = 100.0):
        self.next_id = 1
        self.tracks: Dict[int, Dict] = {}  # track_id -> {bbox, class, last_seen_frame, velocity, history}
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold
        self.distance_threshold = distance_threshold
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
    
    def _distance(self, p1: tuple, p2: tuple) -> float:
        """Calculates Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _predict_position(self, track: Dict) -> tuple:
        """Predicts next position based on velocity"""
        if "velocity" not in track or track["velocity"] is None:
            # If no velocity, return current centroid
            bbox = track["bbox"]
            return self._centroid(bbox)
        
        bbox = track["bbox"]
        current_centroid = self._centroid(bbox)
        velocity = track["velocity"]
        
        # Predict next position: current + velocity
        predicted_x = current_centroid[0] + velocity[0]
        predicted_y = current_centroid[1] + velocity[1]
        
        return (predicted_x, predicted_y)
    
    def _calculate_velocity(self, track: Dict) -> Optional[tuple]:
        """Calculates velocity from track history"""
        if "history" not in track or len(track["history"]) < 2:
            return None
        
        history = track["history"]
        if len(history) < 2:
            return None
        
        # Use last two positions to estimate velocity
        p1 = history[-2]
        p2 = history[-1]
        
        # Simple velocity: difference between last two positions
        vx = p2[0] - p1[0]
        vy = p2[1] - p1[1]
        
        return (vx, vy)
    
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
        
        # Improved matching: IoU + distance to predicted position
        matched = set()
        updated_detections = []
        
        # First pass: calculate velocities for all tracks
        for track_id, track in self.tracks.items():
            if "history" not in track:
                track["history"] = []
            # Add current position to history
            current_centroid = self._centroid(track["bbox"])
            track["history"].append(current_centroid)
            # Limit history size
            if len(track["history"]) > 10:
                track["history"] = track["history"][-10:]
            # Calculate velocity
            track["velocity"] = self._calculate_velocity(track)
        
        for detection in detections:
            bbox = detection["bbox"]
            detection_centroid = self._centroid(bbox)
            
            best_score = -1.0
            best_track_id = None
            best_match_type = None  # "iou" or "distance"
            
            for track_id, track in self.tracks.items():
                if track_id in matched:
                    continue
                
                # Method 1: IoU matching (preferred for overlapping boxes)
                iou = self._iou(bbox, track["bbox"])
                iou_score = iou if iou > self.iou_threshold else 0.0
                
                # Method 2: Distance to predicted position (for motion prediction)
                predicted_pos = self._predict_position(track)
                distance = self._distance(detection_centroid, predicted_pos)
                distance_score = 0.0
                if distance < self.distance_threshold:
                    # Normalize distance score (closer = higher score)
                    distance_score = 1.0 - (distance / self.distance_threshold)
                
                # Combined score: prefer IoU if high, otherwise use distance
                if iou_score > 0.3:
                    score = iou_score * 1.5  # Boost IoU score
                    match_type = "iou"
                else:
                    score = distance_score
                    match_type = "distance"
                
                if score > best_score and (iou_score > self.iou_threshold or distance_score > 0.3):
                    best_score = score
                    best_track_id = track_id
                    best_match_type = match_type
            
            if best_track_id is not None:
                # Update existing track
                detection["track_id"] = best_track_id
                track = self.tracks[best_track_id]
                
                # Update track with new detection
                track["bbox"] = bbox
                track["class"] = detection["class"]
                track["last_seen_frame"] = self.frame_count
                
                # Update history
                if "history" not in track:
                    track["history"] = []
                track["history"].append(detection_centroid)
                if len(track["history"]) > 10:
                    track["history"] = track["history"][-10:]
                
                # Recalculate velocity
                track["velocity"] = self._calculate_velocity(track)
                
                matched.add(best_track_id)
                logger.debug(f"Matched detection to track {best_track_id} using {best_match_type} (score: {best_score:.2f})")
            else:
                # Create new track
                track_id = self.next_id
                self.next_id += 1
                detection["track_id"] = track_id
                self.tracks[track_id] = {
                    "bbox": bbox,
                    "class": detection["class"],
                    "last_seen_frame": self.frame_count,
                    "history": [detection_centroid],
                    "velocity": None
                }
                logger.debug(f"Created new track {track_id}")
            
            updated_detections.append(detection)
        
        return updated_detections

