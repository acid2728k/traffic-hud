# Быстрый старт Traffic HUD

## Шаг 1: Настройка окружения

```bash
cd backend
cp .env.example .env
# Отредактируйте .env при необходимости
```

## Шаг 2: Получение тестового видео

### Вариант A: Использовать существующее видео

Поместите видеофайл в `backend/test_video.mp4`:

```bash
cp /path/to/your/video.mp4 backend/test_video.mp4
```

### Вариант B: Скачать тестовое видео

```bash
cd backend
./download_test_video.sh
```

### Вариант C: Использовать YouTube Live

В `backend/.env` установите:

```env
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI
```

## Шаг 3: Калибровка ROI (опционально)

Если используете свое видео, откройте `backend/roi_config.json` и настройте координаты под ваше видео.

См. [CALIBRATION.md](./CALIBRATION.md) для подробных инструкций.

## Шаг 4: Запуск

```bash
# Из корневой директории проекта
docker compose up --build
```

## Шаг 5: Открыть в браузере

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Настройка параметров

Отредактируйте `backend/.env`:

```env
# FPS обработки (рекомендуется 10 для CPU, можно увеличить до 15)
FPS=10

# Порог уверенности детекции (0.15-0.5, чем ниже - тем больше детекций)
CONFIDENCE_THRESHOLD=0.25

# TTL событий в часах (сколько хранить события)
EVENT_TTL_HOURS=24
```

## Проверка работы

1. Откройте http://localhost:3000
2. Проверьте статус: должен быть "STREAM: LIVE"
3. Наблюдайте события в панелях
4. Кликните на событие для просмотра деталей

## Troubleshooting

### Видео не загружается

```bash
# Проверьте путь к файлу
ls -la backend/test_video.mp4

# Проверьте логи
docker compose logs backend
```

### Нет детекций

1. Убедитесь, что ROI настроен правильно
2. Попробуйте снизить `CONFIDENCE_THRESHOLD` до 0.15
3. Проверьте, что в видео есть транспортные средства

### Неправильный подсчет

1. Перекалибруйте ROI (см. CALIBRATION.md)
2. Проверьте направление движения в roi_config.json
3. Убедитесь, что counting line находится на пути движения

## Дополнительная документация

- [README.md](./README.md) - Полная документация
- [CALIBRATION.md](./CALIBRATION.md) - Калибровка ROI
- [TESTING.md](./TESTING.md) - Подробное руководство по тестированию

