import cv2
import numpy as np
from typing import Tuple, Optional


def detect_plate_region(bbox: Tuple[int, int, int, int], frame_height: int, frame_width: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Эвристическое определение области номерного знака.
    Возвращает (x1, y1, x2, y2) или None.
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    
    # Номер обычно в нижней центральной части автомобиля
    # Примерно 10-20% от высоты bbox, в центре по ширине
    plate_height = int(height * 0.15)
    plate_width = int(width * 0.4)
    
    plate_x1 = x1 + (width - plate_width) // 2
    plate_y1 = y2 - plate_height - int(height * 0.05)
    plate_x2 = plate_x1 + plate_width
    plate_y2 = plate_y1 + plate_height
    
    # Проверка границ
    plate_x1 = max(0, plate_x1)
    plate_y1 = max(0, plate_y1)
    plate_x2 = min(frame_width, plate_x2)
    plate_y2 = min(frame_height, plate_y2)
    
    if plate_x2 > plate_x1 and plate_y2 > plate_y1:
        return (plate_x1, plate_y1, plate_x2, plate_y2)
    return None


def blur_plate_region(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Размывает область номерного знака в кадре.
    """
    frame_height, frame_width = frame.shape[:2]
    plate_region = detect_plate_region(bbox, frame_height, frame_width)
    
    if plate_region is None:
        # Консервативный подход: размываем нижнюю центральную часть
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        plate_height = int(height * 0.2)
        plate_width = int(width * 0.5)
        plate_x1 = max(0, x1 + (width - plate_width) // 2)
        plate_y1 = max(0, y2 - plate_height)
        plate_x2 = min(frame_width, plate_x1 + plate_width)
        plate_y2 = min(frame_height, plate_y1 + plate_height)
        plate_region = (plate_x1, plate_y1, plate_x2, plate_y2)
    
    x1, y1, x2, y2 = plate_region
    
    # Применяем сильное размытие (Gaussian blur)
    roi = frame[y1:y2, x1:x2]
    if roi.size > 0:
        blurred = cv2.GaussianBlur(roi, (51, 51), 0)
        frame[y1:y2, x1:x2] = blurred
    
    return frame

