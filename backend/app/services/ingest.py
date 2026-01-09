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
        self.frame_skip = max(1, int(30 / self.fps))  # Frame skip for performance
        
    def _get_youtube_stream_url(self, url: str) -> str:
        """Gets direct HLS/manifest URL via yt-dlp with retries"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                ydl_opts = {
                    'format': 'worst[height<=480]/worst[height<=720]/worst',  # Lower quality for faster connection
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 20,  # Shorter timeout
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Try mobile client
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    # Try to get HLS URL or direct link
                    if 'url' in info:
                        stream_url = info['url']
                        logger.info(f"Successfully got YouTube stream URL (attempt {attempt + 1})")
                        return stream_url
                    elif 'requested_formats' in info and len(info['requested_formats']) > 0:
                        stream_url = info['requested_formats'][0].get('url', '')
                        if stream_url:
                            logger.info(f"Successfully got YouTube stream URL from formats (attempt {attempt + 1})")
                            return stream_url
                    else:
                        raise ValueError("Could not extract stream URL from YouTube")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    import time
                    time.sleep(2)  # Wait before retry
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {e}")
                    raise ValueError(f"Failed to get YouTube stream after {max_retries} attempts: {e}")
    
    def _open_stream(self):
        """Opens video stream depending on source type"""
        if self.source_type == "file":
            if not self.source_file or not os.path.exists(self.source_file):
                raise FileNotFoundError(f"Video file not found: {self.source_file}")
            self.cap = cv2.VideoCapture(self.source_file)
            
        elif self.source_type == "youtube_url":
            if not self.source_url:
                raise ValueError("YouTube URL not provided")
            logger.info(f"Opening YouTube stream: {self.source_url}")
            try:
                stream_url = self._get_youtube_stream_url(self.source_url)
                logger.info(f"Got stream URL, opening with OpenCV...")
                # Use OpenCV for YouTube
                self.cap = cv2.VideoCapture(stream_url)
                # Set connection timeout
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000)
                # Try to read a frame to verify connection
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    logger.warning("Failed to read test frame, retrying...")
                    self.cap.release()
                    self.cap = cv2.VideoCapture(stream_url)
                    self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000)
                
                if not self.cap.isOpened():
                    logger.error("Failed to open YouTube stream with OpenCV")
                    raise ValueError("Failed to open YouTube stream. Consider using HLS URL or local file.")
                logger.info("YouTube stream opened successfully")
            except Exception as e:
                logger.error(f"Error opening YouTube stream: {e}")
                # Don't raise immediately - let the retry mechanism handle it
                raise
            
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
        """Reads next frame"""
        if self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return None
            # Frame skip
            for _ in range(self.frame_skip - 1):
                self.cap.read()
            return frame
        return None
    
    def is_opened(self) -> bool:
        """Checks if stream is opened"""
        return self.cap is not None and self.cap.isOpened()
    
    def release(self):
        """Releases resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_fps(self) -> float:
        """Returns stream FPS"""
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 30.0
    
    def get_size(self) -> tuple:
        """Returns frame size (width, height)"""
        if self.cap:
            return (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        return (1920, 1080)

