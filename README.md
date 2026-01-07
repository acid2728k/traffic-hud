# TRAFFIC HUD

Production-quality MVP системы подсчета и анализа дорожного трафика в реальном времени с HUD интерфейсом.

## Описание

TRAFFIC HUD (Head-Up Display) - система для автоматического подсчета транспортных средств на дороге с визуализацией в стиле терминала. Система:

- Детектирует и отслеживает транспортные средства (car, truck, bus, motorcycle)
- Подсчитывает трафик по двум направлениям (каждое по 3 полосы)
- Определяет тип ТС, цвет, марку/модель (если возможно)
- Сохраняет snapshots для левой стороны (с автоматическим размытием номеров)
- Отображает статистику за последний час и список последних 50 событий
- Работает в реальном времени через WebSocket

## Архитектура

```
traffic-hud/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # REST API + WebSocket
│   │   ├── core/     # Конфигурация
│   │   ├── models/   # SQLModel модели
│   │   ├── services/ # Video ingest, detection, tracking, counting
│   │   └── utils/    # Color classifier, plate blur, etc.
│   └── roi_config.json
├── frontend/         # React + Vite + TypeScript
│   └── src/
│       ├── components/ # HUD компоненты
│       ├── services/  # API client, WebSocket
│       └── types/      # TypeScript типы
└── docker-compose.yml
```

## Быстрый старт

### Требования

- Docker и Docker Compose
- (Опционально) Локальный видеофайл для тестирования

### Запуск через Docker

1. Клонируйте репозиторий:
```bash
git clone https://github.com/acid2728k/traffic-hud.git
cd traffic-hud
```

2. Создайте файл `.env` в директории `backend/`:
```bash
cd backend
cp .env.example .env
```

3. Настройте источник видео в `.env`:
```env
# Вариант 1: Локальный файл (для тестирования)
VIDEO_SOURCE_TYPE=file
VIDEO_SOURCE_FILE=./test_video.mp4

# Вариант 2: YouTube Live
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI

# Вариант 3: HLS поток
VIDEO_SOURCE_TYPE=hls_url
VIDEO_SOURCE_URL=https://example.com/stream.m3u8

# Вариант 4: RTSP поток
VIDEO_SOURCE_TYPE=rtsp_url
VIDEO_SOURCE_URL=rtsp://example.com/stream

# Настройки обработки
FPS=10
```

4. Запустите через Docker Compose:
```bash
cd ..
docker compose up --build
```

5. Откройте в браузере:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Калибровка ROI (Region of Interest)

Для корректной работы системы нужно настроить области интереса (ROI) и линии подсчета в файле `backend/roi_config.json`.

### Структура конфигурации

```json
{
  "left_side": {
    "name": "LEFT SIDE (TOWARD CAMERA)",
    "direction": "toward_camera",
    "roi": {
      "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    },
    "counting_line": {
      "start": [x1, y1],
      "end": [x2, y2],
      "direction": "toward_camera"
    },
    "lanes": [
      {
        "id": 1,
        "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
      },
      // ... еще 2 полосы
    ]
  },
  "right_side": {
    // аналогично для правой стороны
    "direction": "away_from_camera"
  }
}
```

### Как определить координаты

1. **Запустите систему с тестовым видео**
2. **Откройте видео в любом видеоплеере** и определите координаты в пикселях:
   - ROI (область интереса): полигон, охватывающий всю дорогу для каждой стороны
   - Counting line: линия, которую пересекают автомобили (обычно горизонтальная или диагональная)
   - Lanes: три полигона для каждой полосы движения

3. **Используйте инструменты для разметки** (например, LabelImg, CVAT) или определите координаты вручную:
   - Откройте кадр видео в графическом редакторе
   - Определите координаты точек (x, y) в пикселях
   - Вставьте в `roi_config.json`

4. **Пример координат** (для видео 1920x1080):
   - Левая сторона: ROI может быть [100, 200, 900, 800]
   - Линия подсчета: от [200, 400] до [800, 400] (горизонтальная)
   - Полосы: разделите ROI на 3 равные части по ширине

### Направления

- `toward_camera`: движение к камере (y координата уменьшается при пересечении линии)
- `away_from_camera`: движение от камеры (y координата увеличивается)

## API Endpoints

### REST API

- `GET /api/stats` - Статистика за последний час
- `GET /api/events?side=left|right&limit=50` - Список событий
- `GET /api/events/{id}` - Детали события
- `GET /snapshots/{filename}` - Получить snapshot

### WebSocket

- `WS /ws/events` - Real-time события
  - Сообщения: `{"type": "event_created", "payload": {...}}`

## Privacy & Compliance

⚠️ **ВАЖНО**: Система разработана с учетом приватности:

1. **НЕ выполняет OCR госномеров** - номерные знаки не распознаются и не хранятся
2. **Автоматическое размытие номеров** - все snapshots автоматически размывают область номерного знака
3. **Обезличенные данные** - хранятся только агрегатные данные и события без идентификаторов

## Разработка

### Локальная разработка (без Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Создайте .env файл
cp .env.example .env

# Запустите
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Тестирование

Для тестирования используйте локальный видеофайл:

1. Поместите видеофайл в `backend/test_video.mp4`
2. Установите в `.env`: `VIDEO_SOURCE_TYPE=file`
3. Запустите систему

## Производительность

- **CPU**: Работает на CPU, ожидаемая производительность 5-12 FPS
- **GPU** (опционально): При наличии CUDA можно ускорить YOLOv8
- **FPS**: Настраивается через `FPS` в `.env` (рекомендуется 10)

## Структура базы данных

SQLite база данных `traffic_events.db` содержит таблицу `trafficevent`:

- `id` - Уникальный ID
- `ts` - Временная метка
- `side` - Сторона (left/right)
- `lane` - Полоса (1-3)
- `direction` - Направление
- `vehicle_type` - Тип ТС
- `color` - Цвет
- `make_model` - Марка/модель
- `make_model_conf` - Уверенность
- `snapshot_path` - Путь к snapshot (только для left)
- `bbox` - Координаты bbox (JSON)
- `track_id` - ID трека

## Очистка данных

События хранятся 24 часа (настраивается через `EVENT_TTL_HOURS`). Старые записи и snapshots автоматически удаляются.

## Troubleshooting

### Проблема: Видео не загружается

- Проверьте путь к файлу в `.env`
- Для YouTube: убедитесь, что URL доступен
- Для RTSP/HLS: проверьте доступность потока

### Проблема: Нет детекций

- Проверьте, что ROI настроен правильно
- Убедитесь, что видео содержит транспортные средства
- Проверьте логи backend

### Проблема: Неправильный подсчет

- Перекалибруйте ROI и counting line
- Проверьте направление движения в конфиге
- Убедитесь, что линии подсчета правильно расположены

## Лицензия

MIT

## Контакты

Проект: https://github.com/acid2728k/traffic-hud
