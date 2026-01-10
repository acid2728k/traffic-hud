import cv2
import numpy as np
from typing import Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available. License plate recognition will be disabled.")


def preprocess_plate_image(plate_roi: np.ndarray) -> np.ndarray:
    """
    Preprocesses license plate image for better OCR recognition.
    """
    # Convert to grayscale if needed
    if len(plate_roi.shape) == 3:
        gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_roi.copy()
    
    # Resize if too small (OCR works better on larger images)
    h, w = gray.shape
    if h < 50 or w < 100:
        scale = max(50 / h, 100 / w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    
    return denoised


def recognize_plate_number(plate_roi: np.ndarray) -> str:
    """
    Recognizes license plate number from plate region image.
    Returns recognized number or "XXXXX" if recognition fails.
    """
    if not TESSERACT_AVAILABLE:
        return "XXXXX"
    
    try:
        # Preprocess image
        processed = preprocess_plate_image(plate_roi)
        
        # Configure Tesseract for license plates
        # Use whitelist of common characters: A-Z, 0-9, and some common symbols
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Try OCR
        text = pytesseract.image_to_string(processed, config=custom_config)
        
        # Clean up text
        text = text.strip().upper()
        # Remove spaces and special characters, keep only alphanumeric
        text = re.sub(r'[^A-Z0-9]', '', text)
        
        # Validate: should be 5-8 characters (typical license plate length)
        if len(text) >= 3 and len(text) <= 10:
            # Filter out common OCR errors
            text = text.replace('0', 'O').replace('1', 'I').replace('5', 'S')
            return text
        else:
            return "XXXXX"
            
    except Exception as e:
        logger.warning(f"Error recognizing plate number: {e}")
        return "XXXXX"


def detect_plate_contours(vehicle_roi: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    Detects license plate using contour analysis.
    Returns (x, y, w, h) relative to vehicle_roi or None.
    """
    # Convert to grayscale
    if len(vehicle_roi.shape) == 3:
        gray = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = vehicle_roi.copy()
    
    # Apply adaptive threshold to find text-like regions
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Morphological operations to connect text characters
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Filter contours by aspect ratio and size (license plates are typically wide rectangles)
    plate_candidates = []
    roi_h, roi_w = gray.shape
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter by size (should be significant but not too large)
        # License plates are typically 15-50% of vehicle width and 5-20% of height
        if w < roi_w * 0.12 or h < roi_h * 0.04:
            continue
        if w > roi_w * 0.6 or h > roi_h * 0.25:
            continue
        
        # Filter by aspect ratio (plates are typically 2:1 to 5:1 width:height)
        aspect_ratio = w / h if h > 0 else 0
        if 1.8 <= aspect_ratio <= 5.5:  # More strict aspect ratio
            # Prefer contours in lower 70-95% of vehicle (not just lower half)
            y_ratio = y / roi_h if roi_h > 0 else 0
            if y_ratio >= 0.70:  # Lower 30% of vehicle (where plates actually are)
                # Calculate area for sorting
                area = w * h
                plate_candidates.append((x, y, w, h, aspect_ratio, y_ratio, area))
    
    if not plate_candidates:
        return None
    
    # Sort by: 1) lower position (higher y_ratio), 2) better aspect ratio (closer to 3:1), 3) larger area
    # Prefer aspect ratio around 3:1 (typical for license plates)
    plate_candidates.sort(key=lambda c: (
        -c[5],  # Lower position (higher y_ratio) - most important
        -abs(c[4] - 3.0),  # Aspect ratio closer to 3:1
        -c[6]  # Larger area
    ))
    
    # Return best candidate
    best = plate_candidates[0]
    return (best[0], best[1], best[2], best[3])


def extract_plate_region(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    """
    Extracts license plate region from vehicle bbox using improved detection.
    First tries contour-based detection, falls back to heuristic if needed.
    Returns plate ROI or None if not found.
    """
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]
    
    # Ensure bbox is within frame bounds
    x1 = max(0, min(x1, w))
    y1 = max(0, min(y1, h))
    x2 = max(0, min(x2, w))
    y2 = max(0, min(y2, h))
    
    if x2 <= x1 or y2 <= y1:
        return None
    
    # Extract vehicle region
    vehicle_roi = frame[y1:y2, x1:x2].copy()
    
    if vehicle_roi.size == 0:
        return None
    
    # Try contour-based detection first
    plate_rect = detect_plate_contours(vehicle_roi)
    
    if plate_rect:
        px, py, pw, ph = plate_rect
        # Add some padding
        padding = 5
        px = max(0, px - padding)
        py = max(0, py - padding)
        pw = min(vehicle_roi.shape[1] - px, pw + padding * 2)
        ph = min(vehicle_roi.shape[0] - py, ph + padding * 2)
        
        plate_roi = vehicle_roi[py:py+ph, px:px+pw]
        if plate_roi.size > 0:
            logger.debug(f"Plate detected using contour analysis: {px}, {py}, {pw}, {ph}")
            return plate_roi
    
    # Fallback to improved heuristic - ALWAYS return something
    # License plates are typically:
    # - In the bottom 10-20% of vehicle height (not 25%!)
    # - In the central 40-50% of vehicle width (not 55%!)
    # - Positioned at 75-90% down from top of vehicle
    width = x2 - x1
    height = y2 - y1
    
    # More precise dimensions for license plate
    plate_height = max(int(height * 0.15), 15)  # 15% of height, at least 15 pixels
    plate_width = max(int(width * 0.45), 40)    # 45% of width, at least 40 pixels
    
    # Position: bottom central part - more precise
    # Start from 80% down (not 65%) - plates are at the very bottom
    plate_x1 = max(0, x1 + int((width - plate_width) / 2))
    plate_y1 = max(0, y1 + int(height * 0.80))  # Start from 80% down (bottom of vehicle)
    plate_x2 = min(w, plate_x1 + plate_width)
    plate_y2 = min(h, plate_y1 + plate_height)
    
    # Ensure we don't go beyond vehicle bounds
    plate_y2 = min(plate_y2, y2)  # Don't go below vehicle bottom
    
    # Ensure we have valid dimensions
    if plate_x2 <= plate_x1:
        plate_x2 = plate_x1 + plate_width
    if plate_y2 <= plate_y1:
        plate_y2 = plate_y1 + plate_height
    
    # Final boundary check
    plate_x1 = max(0, min(plate_x1, w - 1))
    plate_y1 = max(0, min(plate_y1, h - 1))
    plate_x2 = max(plate_x1 + 1, min(plate_x2, w))
    plate_y2 = max(plate_y1 + 1, min(plate_y2, h))
    
    if plate_x2 > plate_x1 and plate_y2 > plate_y1:
        plate_roi = frame[plate_y1:plate_y2, plate_x1:plate_x2]
        logger.debug(f"Plate detected using heuristic: {plate_x1}, {plate_y1}, {plate_x2}, {plate_y2}")
        return plate_roi
    
    # Last resort: return a precise region in the bottom-center of the bbox
    logger.warning(f"Could not extract plate region using heuristic, using last resort fallback for bbox {bbox}")
    # Use smaller, more precise region - bottom 15% of vehicle, center 45% width
    fallback_height = max(int(height * 0.15), 15)
    fallback_width = max(int(width * 0.45), 40)
    fallback_x1 = max(0, x1 + (width - fallback_width) // 2)
    fallback_y1 = max(0, y2 - fallback_height - int(height * 0.05))  # 5% margin from bottom
    fallback_x2 = min(w, fallback_x1 + fallback_width)
    fallback_y2 = min(h, fallback_y1 + fallback_height)
    
    if fallback_x2 > fallback_x1 and fallback_y2 > fallback_y1:
        plate_roi = frame[fallback_y1:fallback_y2, fallback_x1:fallback_x2]
        logger.debug(f"Using last resort fallback: {fallback_x1}, {fallback_y1}, {fallback_x2}, {fallback_y2}")
        return plate_roi
    
    # Absolute last resort: return bottom 20% of vehicle, center 50% width
    logger.error(f"All plate extraction methods failed for bbox {bbox}, returning bottom vehicle region")
    bottom_start = int(vehicle_roi.shape[0] * 0.8)
    center_start = int(vehicle_roi.shape[1] * 0.25)
    center_end = int(vehicle_roi.shape[1] * 0.75)
    return vehicle_roi[bottom_start:, center_start:center_end]
