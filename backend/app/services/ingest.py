import cv2
import subprocess
import os
import yt_dlp
import logging
from typing import Optional
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoIngest:
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.process: Optional[subprocess.Popen] = None
        self.source_type = settings.video_source_type
        self.source_url = settings.video_source_url or settings.youtube_url
        self.source_file = settings.video_source_file
        self.fps = settings.fps
        self.frame_skip = max(1, int(30 / self.fps))  # Пропуск кадров для производительности
        
    def _get_youtube_stream_url(self, url: str) -> str:
        """Получает прямую ссылку на HLS/manifest через yt-dlp"""
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('url', '')
        except Exception as e:
            logger.error(f"Error getting YouTube stream URL: {e}")
            raise
    
    def _open_stream(self):
        """Открывает видеопоток в зависимости от типа источника"""
        if self.source_type == "file":
            if not self.source_file or not os.path.exists(self.source_file):
                raise FileNotFoundError(f"Video file not found: {self.source_file}")
            self.cap = cv2.VideoCapture(self.source_file)
            
        elif self.source_type == "youtube_url":
            if not self.source_url:
                raise ValueError("YouTube URL not provided")
            stream_url = self._get_youtube_stream_url(self.source_url)
            # Используем OpenCV для YouTube (может работать с некоторыми потоками)
            # Альтернатива: использовать ffmpeg pipe, но это сложнее
            self.cap = cv2.VideoCapture(stream_url)
            if not self.cap.isOpened():
                # Fallback: используем yt-dlp для скачивания и локального воспроизведения
                raise ValueError("Failed to open YouTube stream. Consider using HLS URL or local file.")
            
        elif self.source_type == "hls_url":
            if not self.source_url:
                raise ValueError("HLS URL not provided")
            self.cap = cv2.VideoCapture(self.source_url)
            
        elif self.source_type == "rtsp_url":
            if not self.source_url:
                raise ValueError("RTSP URL not provided")
            self.cap = cv2.VideoCapture(self.source_url)
            
        else:
            raise ValueError(f"Unknown source type: {self.source_type}")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Читает следующий кадр"""
        if self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return None
            # Пропуск кадров
            for _ in range(self.frame_skip - 1):
                self.cap.read()
            return frame
        return None
    
    def is_opened(self) -> bool:
        """Проверяет, открыт ли поток"""
        return self.cap is not None and self.cap.isOpened()
    
    def release(self):
        """Освобождает ресурсы"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_fps(self) -> float:
        """Возвращает FPS потока"""
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 30.0
    
    def get_size(self) -> tuple:
        """Возвращает размер кадра (width, height)"""
        if self.cap:
            return (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        return (1920, 1080)

