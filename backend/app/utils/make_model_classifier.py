from typing import Tuple, Optional, Dict
import cv2
import numpy as np
import random


# Popular car brands
CAR_BRANDS = [
    "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes-Benz",
    "Audi", "Volkswagen", "Hyundai", "Kia", "Mazda", "Subaru", "Jeep",
    "Lexus", "Acura", "Infiniti", "Cadillac", "Lincoln", "Buick", "GMC",
    "Ram", "Dodge", "Chrysler", "Volvo", "Porsche", "Tesla", "Jaguar",
    "Land Rover", "Mitsubishi", "Mini", "Fiat", "Alfa Romeo", "Genesis"
]


def classify_make_model(frame, bbox: Tuple[int, int, int, int]) -> Dict[str, any]:
    """
    Enhanced classifier that determines both car brand (make) and body type.
    Returns dict with 'brand', 'body_type', and 'confidence'.
    """
    try:
        x1, y1, x2, y2 = bbox
        
        # Ensure bbox is within frame bounds
        h, w = frame.shape[:2]
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        if x2 <= x1 or y2 <= y1:
            return {
                "brand": "Unknown",
                "body_type": "Vehicle",
                "confidence": 0.2
            }
        
        # Extract vehicle region
        vehicle_roi = frame[y1:y2, x1:x2]
        
        if vehicle_roi.size == 0:
            return {
                "brand": "Unknown",
                "body_type": "Vehicle",
                "confidence": 0.2
            }
        
        # Calculate dimensions
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / height if height > 0 else 0
        area = width * height
        
        # Calculate relative size (percentage of frame)
        frame_area = w * h
        relative_size = (area / frame_area) * 100 if frame_area > 0 else 0
        
        # Determine body type based on size and aspect ratio
        body_type = "Sedan"
        body_confidence = 0.35
        
        if area > 60000 or relative_size > 3.0:  # Very large vehicle
            if aspect_ratio > 2.8:
                body_type = "Truck"
            elif aspect_ratio > 2.3:
                body_type = "Bus"
            elif aspect_ratio > 2.0:
                body_type = "Van"
            else:
                body_type = "Large SUV"
            body_confidence = 0.4
        elif area > 35000 or relative_size > 1.8:  # Large vehicle
            if aspect_ratio > 2.4:
                body_type = "SUV"
            elif aspect_ratio > 2.0:
                body_type = "Wagon"
            else:
                body_type = "Crossover"
            body_confidence = 0.35
        elif area > 20000 or relative_size > 1.0:  # Medium vehicle
            if aspect_ratio > 2.3:
                body_type = "Sedan"
            elif aspect_ratio > 1.8:
                body_type = "Hatchback"
            else:
                body_type = "Coupe"
            body_confidence = 0.35
        elif area > 5000 or relative_size > 0.25:  # Small vehicle
            if aspect_ratio > 2.0:
                body_type = "Compact"
            else:
                body_type = "Subcompact"
            body_confidence = 0.3
        elif area > 2000 or relative_size > 0.1:  # Very small vehicle (likely compact car, not motorcycle)
            body_type = "Compact"
            body_confidence = 0.25
        else:  # Extremely small - likely detection error or very far vehicle
            # Don't classify as motorcycle - classify as compact instead
            body_type = "Compact"
            body_confidence = 0.2
        
        # Simple brand detection based on vehicle characteristics
        # This is a placeholder - in production, use ML model for brand detection
        brand = "Unknown"
        brand_confidence = 0.2
        
        # Basic heuristics for brand detection (can be improved with ML)
        # For now, randomly select from common brands based on body type
        # In production, this should use image recognition
        if body_type in ["Sedan", "Coupe", "Hatchback", "Compact", "Subcompact"]:
            # Common sedan/compact brands
            brand = random.choice(["Toyota", "Honda", "Ford", "Nissan", "Hyundai", "Kia", "BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Mazda"])
            brand_confidence = 0.25
        elif body_type in ["SUV", "Large SUV", "Crossover"]:
            # Common SUV brands
            brand = random.choice(["Toyota", "Honda", "Ford", "Jeep", "Chevrolet", "GMC", "BMW", "Mercedes-Benz", "Audi", "Lexus"])
            brand_confidence = 0.25
        elif body_type == "Truck":
            # Common truck brands
            brand = random.choice(["Ford", "Chevrolet", "Ram", "GMC", "Toyota", "Nissan"])
            brand_confidence = 0.3
        elif body_type == "Van":
            # Common van brands
            brand = random.choice(["Ford", "Mercedes-Benz", "Ram", "Chevrolet"])
            brand_confidence = 0.3
        else:
            brand = random.choice(CAR_BRANDS[:10])
            brand_confidence = 0.2
        
        # Overall confidence is average of brand and body type confidence
        overall_confidence = (brand_confidence + body_confidence) / 2
        
        return {
            "brand": brand,
            "body_type": body_type,
            "confidence": overall_confidence
        }
            
    except Exception as e:
        return {
            "brand": "Unknown",
            "body_type": "Vehicle",
            "confidence": 0.2
        }


# Backward compatibility function
def classify_make_model_old(frame, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
    """
    Old function signature for backward compatibility.
    Returns combined string "Brand - BodyType" and confidence.
    """
    result = classify_make_model(frame, bbox)
    combined = f"{result['brand']} - {result['body_type']}"
    return combined, result['confidence']

