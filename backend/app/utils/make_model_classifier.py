from typing import Tuple, Optional
import cv2
import numpy as np


def classify_make_model(frame, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
    """
    Basic make/model classifier using simple heuristics.
    Can be improved with ML model later.
    """
    try:
        x1, y1, x2, y2 = bbox
        # Extract vehicle region
        vehicle_roi = frame[y1:y2, x1:x2]
        
        if vehicle_roi.size == 0:
            return None, 0.0
        
        # Simple heuristics based on size and aspect ratio
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / height if height > 0 else 0
        area = width * height
        
        # Very basic classification based on size and shape
        # This is a placeholder - can be improved with actual ML model
        if area > 50000:  # Large vehicle
            if aspect_ratio > 2.5:
                return "Truck", 0.3
            elif aspect_ratio > 2.0:
                return "Van", 0.3
            else:
                return "SUV", 0.3
        elif area > 20000:  # Medium vehicle
            if aspect_ratio > 2.2:
                return "Sedan", 0.3
            else:
                return "Hatchback", 0.3
        else:  # Small vehicle
            return "Compact", 0.3
            
    except Exception as e:
        # Return None on any error
        return None, 0.0

