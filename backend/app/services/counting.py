import json
import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import logging
from app.core.config import settings
from app.models.database import TrafficEvent, get_session
from app.utils.plate_blur import blur_plate_region
from app.utils.color_classifier import classify_color
from app.utils.make_model_classifier import classify_make_model

logger = logging.getLogger(__name__)


class TrafficCounter:
    def __init__(self):
        self.roi_config = self._load_roi_config()
        self.counted_tracks: Dict[int, bool] = {}  # track_id -> уже посчитан
        self.track_history: Dict[int, List[Tuple[float, float]]] = {}  # track_id -> список (x, y) центров
        
    def _load_roi_config(self) -> Dict:
        """Загружает конфигурацию ROI из JSON"""
        config_path = settings.roi_config_path
        if not os.path.exists(config_path):
            logger.warning(f"ROI config not found: {config_path}, using defaults")
            return self._default_config()
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _default_config(self) -> Dict:
        """Возвращает конфигурацию по умолчанию"""
        return {
            "left_side": {
                "name": "LEFT SIDE (TOWARD CAMERA)",
                "direction": "toward_camera",
                "roi": {"polygon": [[0, 0], [640, 0], [640, 480], [0, 480]]},
                "counting_line": {"start": [100, 240], "end": [540, 240], "direction": "toward_camera"},
                "lanes": [
                    {"id": 1, "polygon": [[0, 0], [213, 0], [213, 480], [0, 480]]},
                    {"id": 2, "polygon": [[213, 0], [427, 0], [427, 480], [213, 480]]},
                    {"id": 3, "polygon": [[427, 0], [640, 0], [640, 480], [427, 480]]}
                ]
            },
            "right_side": {
                "name": "RIGHT SIDE (AWAY FROM CAMERA)",
                "direction": "away_from_camera",
                "roi": {"polygon": [[0, 0], [640, 0], [640, 480], [0, 480]]},
                "counting_line": {"start": [100, 240], "end": [540, 240], "direction": "away_from_camera"},
                "lanes": [
                    {"id": 1, "polygon": [[0, 0], [213, 0], [213, 480], [0, 480]]},
                    {"id": 2, "polygon": [[213, 0], [427, 0], [427, 480], [213, 480]]},
                    {"id": 3, "polygon": [[427, 0], [640, 0], [640, 480], [427, 480]]}
                ]
            }
        }
    
    def _point_in_polygon(self, point: Tuple[float, float], polygon: List[List[int]]) -> bool:
        """Проверяет, находится ли точка внутри полигона"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _line_intersection(self, line1: Tuple[Tuple[float, float], Tuple[float, float]], 
                          line2: Tuple[Tuple[float, float], Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        """Проверяет пересечение двух отрезков"""
        (x1, y1), (x2, y2) = line1
        (x3, y3), (x4, y4) = line2
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)
        return None
    
    def _get_lane(self, centroid: Tuple[float, float], side: str) -> int:
        """Определяет полосу по центроиду"""
        side_config = self.roi_config[f"{side}_side"]
        for lane in side_config["lanes"]:
            if self._point_in_polygon(centroid, lane["polygon"]):
                return lane["id"]
        return 1  # По умолчанию
    
    def _crossed_counting_line(self, track_id: int, side: str) -> bool:
        """Проверяет, пересек ли трек линию подсчета"""
        if track_id not in self.track_history or len(self.track_history[track_id]) < 2:
            return False
        
        side_config = self.roi_config[f"{side}_side"]
        line_start = side_config["counting_line"]["start"]
        line_end = side_config["counting_line"]["end"]
        direction = side_config["counting_line"]["direction"]
        
        history = self.track_history[track_id]
        
        # Проверяем пересечение между последними двумя точками
        for i in range(len(history) - 1):
            p1 = history[i]
            p2 = history[i + 1]
            
            intersection = self._line_intersection(
                (p1, p2),
                ((line_start[0], line_start[1]), (line_end[0], line_end[1]))
            )
            
            if intersection:
                # Проверяем направление
                if direction == "toward_camera":
                    # Движение к камере: y должен уменьшаться
                    if p2[1] < p1[1]:
                        return True
                else:  # away_from_camera
                    # Движение от камеры: y должен увеличиваться
                    if p2[1] > p1[1]:
                        return True
        
        return False
    
    def process_frame(self, frame: np.ndarray, detections: List[Dict], 
                     on_event: Optional[Callable[[Dict], None]] = None) -> List[Dict]:
        """
        Обрабатывает кадр с детекциями и создает события проезда.
        on_event: callback(event_dict) вызывается при новом событии
        """
        events = []
        
        for det in detections:
            track_id = det["track_id"]
            bbox = det["bbox"]
            vehicle_type = det["class"]
            
            # Вычисляем центроид
            x1, y1, x2, y2 = bbox
            centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Обновляем историю трека
            if track_id not in self.track_history:
                self.track_history[track_id] = []
            self.track_history[track_id].append(centroid)
            # Ограничиваем историю
            if len(self.track_history[track_id]) > 10:
                self.track_history[track_id] = self.track_history[track_id][-10:]
            
            # Определяем сторону
            side = None
            for side_name in ["left", "right"]:
                side_config = self.roi_config[f"{side_name}_side"]
                roi_polygon = side_config["roi"]["polygon"]
                if self._point_in_polygon(centroid, roi_polygon):
                    side = side_name
                    break
            
            if side is None:
                continue
            
            # Проверяем пересечение линии подсчета
            if not self.counted_tracks.get(track_id, False):
                if self._crossed_counting_line(track_id, side):
                    self.counted_tracks[track_id] = True
                    
                    # Определяем полосу
                    lane = self._get_lane(centroid, side)
                    
                    # Классифицируем цвет
                    color = classify_color(frame, tuple(bbox))
                    
                    # Классифицируем марку/модель
                    make_model, make_model_conf = classify_make_model(frame, tuple(bbox))
                    
                    # Создаем snapshot для левой стороны
                    snapshot_path = None
                    if side == "left":
                        snapshot_path = self._save_snapshot(frame, bbox, track_id)
                    
                    # Создаем событие
                    event = {
                        "ts": datetime.utcnow(),
                        "side": side,
                        "lane": lane,
                        "direction": self.roi_config[f"{side}_side"]["direction"],
                        "vehicle_type": vehicle_type,
                        "color": color,
                        "make_model": make_model if make_model else "Unknown",
                        "make_model_conf": make_model_conf,
                        "snapshot_path": snapshot_path,
                        "bbox": json.dumps(bbox),
                        "track_id": track_id,
                        "source_meta": json.dumps({"confidence": det.get("confidence", 0.0)})
                    }
                    
                    # Сохраняем в БД
                    self._save_event(event)
                    
                    events.append(event)
                    
                    # Вызываем callback
                    if on_event:
                        on_event(event)
        
        return events
    
    def _save_snapshot(self, frame: np.ndarray, bbox: List[int], track_id: int) -> str:
        """Сохраняет snapshot с размытием номера"""
        x1, y1, x2, y2 = bbox
        # Добавляем небольшой отступ
        padding = 10
        h, w = frame.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        snapshot = frame[y1:y2, x1:x2].copy()
        
        # Размываем номер
        snapshot = blur_plate_region(snapshot, (0, 0, x2 - x1, y2 - y1))
        
        # Сохраняем
        os.makedirs(settings.snapshots_dir, exist_ok=True)
        filename = f"snapshot_{track_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        filepath = os.path.join(settings.snapshots_dir, filename)
        cv2.imwrite(filepath, snapshot)
        
        return f"/snapshots/{filename}"
    
    def _save_event(self, event: Dict):
        """Сохраняет событие в БД"""
        try:
            with get_session() as session:
                db_event = TrafficEvent(**event)
                session.add(db_event)
                session.commit()
        except Exception as e:
            logger.error(f"Error saving event: {e}")

