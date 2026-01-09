import cv2
import numpy as np
from typing import List, Dict, Tuple

# Colors for different vehicle types
VEHICLE_COLORS = {
    "car": (0, 255, 0),      # Green
    "truck": (255, 0, 0),    # Blue
    "bus": (255, 0, 255),    # Magenta
    "motorcycle": (0, 255, 255),  # Yellow
}

# Color for tracks
TRACK_COLOR = (0, 255, 255)  # Cyan


def draw_detections(frame: np.ndarray, detections: List[Dict], 
                   show_track_id: bool = True, show_confidence: bool = True) -> np.ndarray:
    """
    Draws bounding boxes and labels on frame.
    
    Args:
        frame: Input frame (BGR)
        detections: List of detections [{"bbox": [x1,y1,x2,y2], "class": "car", "confidence": 0.9, "track_id": 1}, ...]
        show_track_id: Whether to show track_id
        show_confidence: Whether to show confidence
    
    Returns:
        Frame with drawn bounding boxes
    """
    frame_copy = frame.copy()
    
    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) != 4:
            continue
        
        x1, y1, x2, y2 = map(int, bbox)
        vehicle_type = det.get("class", "unknown")
        confidence = det.get("confidence", 0.0)
        track_id = det.get("track_id", None)
        
        # Select color by vehicle type
        color = VEHICLE_COLORS.get(vehicle_type, (255, 255, 255))
        
        # Draw bounding box
        thickness = 2
        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, thickness)
        
        # Build label text
        label_parts = [vehicle_type.upper()]
        
        if show_confidence:
            label_parts.append(f"{confidence:.2f}")
        
        if show_track_id and track_id is not None:
            label_parts.append(f"ID:{track_id}")
        
        label = " ".join(label_parts)
        
        # Text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Calculate text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Draw text background
        label_y = max(y1 - 10, text_height + 10)
        cv2.rectangle(
            frame_copy,
            (x1, label_y - text_height - 5),
            (x1 + text_width + 5, label_y + baseline),
            color,
            -1  # Filled rectangle
        )
        
        # Draw text
        cv2.putText(
            frame_copy,
            label,
            (x1 + 2, label_y - 2),
            font,
            font_scale,
            (0, 0, 0),  # Black text
            font_thickness,
            cv2.LINE_AA
        )
    
    return frame_copy


def draw_counting_lines(frame: np.ndarray, roi_config: Dict) -> np.ndarray:
    """
    Draws counting lines on frame.
    
    Args:
        frame: Input frame
        roi_config: ROI configuration with counting lines
    
    Returns:
        Frame with drawn lines
    """
    frame_copy = frame.copy()
    
    for side_name in ["left_side", "right_side"]:
        if side_name not in roi_config:
            continue
        
        side_config = roi_config[side_name]
        counting_line = side_config.get("counting_line", {})
        
        if "start" in counting_line and "end" in counting_line:
            start = counting_line["start"]
            end = counting_line["end"]
            
            # Draw counting line (yellow)
            cv2.line(
                frame_copy,
                (int(start[0]), int(start[1])),
                (int(end[0]), int(end[1])),
                (0, 255, 255),  # Yellow
                2
            )
            
            # Line label
            mid_x = (int(start[0]) + int(end[0])) // 2
            mid_y = (int(start[1]) + int(end[1])) // 2
            
            label = side_config.get("name", side_name).upper()
            cv2.putText(
                frame_copy,
                label,
                (mid_x - 50, mid_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                2
            )
    
    return frame_copy
