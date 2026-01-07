#!/bin/bash

# Скрипт для скачивания тестового видео
# Использует yt-dlp для скачивания короткого видео с дорожным движением

echo "Downloading test video for Traffic HUD..."
echo "This will download a short traffic video for testing purposes."

# Пример: скачать короткое видео с YouTube (можно заменить на другой источник)
# Убедитесь, что yt-dlp установлен: pip install yt-dlp

if command -v yt-dlp &> /dev/null; then
    # Скачиваем короткое видео (пример - замените на актуальное видео с дорожным движением)
    # Используем формат mp4 и ограничиваем длину до 2 минут для тестирования
    yt-dlp -f "best[ext=mp4]" \
           --no-playlist \
           --extract-flat \
           --output "test_video.%(ext)s" \
           --max-downloads 1 \
           "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>/dev/null || {
        echo "Error: Could not download video. Using alternative method..."
        echo ""
        echo "Please download a test video manually:"
        echo "1. Find a video with traffic/vehicles (YouTube, etc.)"
        echo "2. Download it and save as 'test_video.mp4' in the backend/ directory"
        echo "3. Or use yt-dlp: yt-dlp -f 'best[ext=mp4]' <VIDEO_URL> -o test_video.mp4"
        exit 1
    }
    
    if [ -f "test_video.mp4" ]; then
        echo "✓ Test video downloaded successfully: test_video.mp4"
        echo "You can now run the system with: docker compose up"
    else
        echo "✗ Video download failed. Please download manually."
    fi
else
    echo "yt-dlp not found. Please install it:"
    echo "  pip install yt-dlp"
    echo ""
    echo "Or download a test video manually:"
    echo "1. Find a video with traffic/vehicles"
    echo "2. Save it as 'test_video.mp4' in the backend/ directory"
fi

