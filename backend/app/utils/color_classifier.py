import cv2
import numpy as np
from typing import Tuple


def classify_color(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
    """
    Классифицирует цвет автомобиля по ROI bbox.
    Возвращает: black, white, gray, red, blue, green, yellow, orange, brown, silver
    """
    x1, y1, x2, y2 = bbox
    roi = frame[y1:y2, x1:x2]
    
    if roi.size == 0:
        return "unknown"
    
    # Конвертируем в HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Вычисляем средний цвет
    mean_hue = np.mean(hsv[:, :, 0])
    mean_sat = np.mean(hsv[:, :, 1])
    mean_val = np.mean(hsv[:, :, 2])
    
    # Классификация
    if mean_val < 30:
        return "black"
    if mean_sat < 30 and mean_val > 200:
        return "white"
    if mean_sat < 30 and 100 < mean_val < 200:
        return "gray"
    if mean_sat < 30 and mean_val > 200:
        return "silver"
    
    # Цветные
    if mean_hue < 10 or mean_hue > 170:
        return "red"
    if 20 < mean_hue < 30:
        return "yellow"
    if 10 < mean_hue < 20:
        return "orange"
    if 50 < mean_hue < 70:
        return "green"
    if 100 < mean_hue < 130:
        return "blue"
    if 15 < mean_hue < 25 and mean_sat < 50:
        return "brown"
    
    return "unknown"

