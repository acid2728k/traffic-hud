import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class VehicleDetector:
    def __init__(self):
        self.model = YOLO(settings.yolo_model)
        self.confidence_threshold = settings.confidence_threshold
        # Vehicle classes in COCO/YOLO: 2=car, 3=motorcycle, 5=bus, 7=truck
        self.vehicle_classes = [2, 3, 5, 7]
        self.class_names = {
            2: "car",
            3: "motorcycle",
            5: "bus",
            7: "truck"
        }
    
    def detect(self, frame: np.ndarray) -> List[dict]:
        """
        Detects vehicles in frame.
        Returns list: [{"bbox": [x1,y1,x2,y2], "class": "car", "confidence": 0.9}, ...]
        """
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                cls = int(boxes.cls[i])
                if cls in self.vehicle_classes:
                    conf = float(boxes.conf[i])
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    detections.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "class": self.class_names[cls],
                        "confidence": conf
                    })
        
        return detections

