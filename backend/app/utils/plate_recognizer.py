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


def extract_plate_region(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    """
    Extracts license plate region from vehicle bbox.
    Returns plate ROI or None if not found.
    """
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]
    
    # Plate is usually in lower central part of vehicle
    width = x2 - x1
    height = y2 - y1
    plate_height = int(height * 0.2)
    plate_width = int(width * 0.5)
    
    plate_x1 = max(0, x1 + (width - plate_width) // 2)
    plate_y1 = max(0, y2 - plate_height - int(height * 0.05))
    plate_x2 = min(w, plate_x1 + plate_width)
    plate_y2 = min(h, plate_y1 + plate_height)
    
    if plate_x2 > plate_x1 and plate_y2 > plate_y1:
        plate_roi = frame[plate_y1:plate_y2, plate_x1:plate_x2]
        return plate_roi
    
    return None
