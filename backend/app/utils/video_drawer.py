import cv2
import numpy as np
from typing import List, Dict, Tuple

# Цвета для разных типов транспорта
VEHICLE_COLORS = {
    "car": (0, 255, 0),      # Зеленый
    "truck": (255, 0, 0),    # Синий
    "bus": (255, 0, 255),    # Пурпурный
    "motorcycle": (0, 255, 255),  # Желтый
}

# Цвет для треков
TRACK_COLOR = (0, 255, 255)  # Циан


def draw_detections(frame: np.ndarray, detections: List[Dict], 
                   show_track_id: bool = True, show_confidence: bool = True) -> np.ndarray:
    """
    Рисует bounding boxes и метки на кадре.
    
    Args:
        frame: Входной кадр (BGR)
        detections: Список детекций [{"bbox": [x1,y1,x2,y2], "class": "car", "confidence": 0.9, "track_id": 1}, ...]
        show_track_id: Показывать ли track_id
        show_confidence: Показывать ли confidence
    
    Returns:
        Кадр с нарисованными bounding boxes
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
        
        # Выбираем цвет по типу транспорта
        color = VEHICLE_COLORS.get(vehicle_type, (255, 255, 255))
        
        # Рисуем bounding box
        thickness = 2
        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, thickness)
        
        # Формируем текст метки
        label_parts = [vehicle_type.upper()]
        
        if show_confidence:
            label_parts.append(f"{confidence:.2f}")
        
        if show_track_id and track_id is not None:
            label_parts.append(f"ID:{track_id}")
        
        label = " ".join(label_parts)
        
        # Размер текста
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Вычисляем размер текста для фона
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Рисуем фон для текста
        label_y = max(y1 - 10, text_height + 10)
        cv2.rectangle(
            frame_copy,
            (x1, label_y - text_height - 5),
            (x1 + text_width + 5, label_y + baseline),
            color,
            -1  # Заполненный прямоугольник
        )
        
        # Рисуем текст
        cv2.putText(
            frame_copy,
            label,
            (x1 + 2, label_y - 2),
            font,
            font_scale,
            (0, 0, 0),  # Черный текст
            font_thickness,
            cv2.LINE_AA
        )
    
    return frame_copy


def draw_counting_lines(frame: np.ndarray, roi_config: Dict) -> np.ndarray:
    """
    Рисует линии подсчета на кадре.
    
    Args:
        frame: Входной кадр
        roi_config: Конфигурация ROI с линиями подсчета
    
    Returns:
        Кадр с нарисованными линиями
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
            
            # Рисуем линию подсчета (желтая)
            cv2.line(
                frame_copy,
                (int(start[0]), int(start[1])),
                (int(end[0]), int(end[1])),
                (0, 255, 255),  # Желтый
                2
            )
            
            # Подпись линии
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
