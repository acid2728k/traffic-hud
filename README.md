# TRAFFIC HUD

Production-quality MVP system for real-time traffic counting and analysis with HUD interface.

## Description

TRAFFIC HUD (Head-Up Display) - system for automatic vehicle counting on roads with terminal-style visualization. The system:

- Detects and tracks vehicles (car, truck, bus, motorcycle)
- Counts traffic in two directions (3 lanes each)
- Determines vehicle type, color, make/model (if possible)
- Saves snapshots for left side (with automatic license plate blurring)
- Displays statistics for the last hour and list of last 50 events
- Works in real-time via WebSocket

## Architecture

```
traffic-hud/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # REST API + WebSocket
│   │   ├── core/     # Configuration
│   │   ├── models/   # SQLModel models
│   │   ├── services/ # Video ingest, detection, tracking, counting
│   │   └── utils/    # Color classifier, plate blur, etc.
│   └── roi_config.json
├── frontend/         # React + Vite + TypeScript
│   └── src/
│       ├── components/ # HUD components
│       ├── services/  # API client, WebSocket
│       └── types/      # TypeScript types
└── docker-compose.yml
```

## Quick Start

📖 **For quick start, see [QUICK_START.md](./QUICK_START.md)**

### Requirements

- Docker and Docker Compose
- (Optional) Local video file for testing

### Running via Docker

1. Clone the repository:
```bash
git clone https://github.com/acid2728k/traffic-hud.git
cd traffic-hud
```

2. Configure `.env` file (already created with default settings):
```bash
cd backend
# .env is already created, but you can edit if needed
nano .env
```

3. Configure video source in `.env`:
```env
# Option 1: Local file (for testing)
VIDEO_SOURCE_TYPE=file
VIDEO_SOURCE_FILE=./test_video.mp4

# Option 2: YouTube Live
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI

# Option 3: HLS stream
VIDEO_SOURCE_TYPE=hls_url
VIDEO_SOURCE_URL=https://example.com/stream.m3u8

# Option 4: RTSP stream (IP camera)
VIDEO_SOURCE_TYPE=rtsp_url
VIDEO_SOURCE_URL=rtsp://example.com/stream

# Processing settings
FPS=10
```

📹 **Detailed IP Camera Setup Guide: [IP_CAMERA_SETUP.md](./IP_CAMERA_SETUP.md)**

4. Start via Docker Compose:
```bash
cd ..
docker compose up --build
```

5. Open in browser:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## ROI Calibration (Region of Interest)

📖 **Detailed guide: [CALIBRATION.md](./CALIBRATION.md)**

For correct system operation, you need to configure regions of interest (ROI) and counting lines in the `backend/roi_config.json` file.

### Configuration Structure

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
      // ... 2 more lanes
    ]
  },
  "right_side": {
    // similar for right side
    "direction": "away_from_camera"
  }
}
```

### How to Determine Coordinates

1. **Run the system with test video**
2. **Open video in any video player** and determine coordinates in pixels:
   - ROI (region of interest): polygon covering the entire road for each side
   - Counting line: line that vehicles cross (usually horizontal or diagonal)
   - Lanes: three polygons for each traffic lane

3. **Use annotation tools** (e.g., LabelImg, CVAT) or determine coordinates manually:
   - Open a video frame in a graphics editor
   - Determine point coordinates (x, y) in pixels
   - Insert into `roi_config.json`

4. **Example coordinates** (for 1920x1080 video):
   - Left side: ROI might be [100, 200, 900, 800]
   - Counting line: from [200, 400] to [800, 400] (horizontal)
   - Lanes: divide ROI into 3 equal parts by width

### Directions

- `toward_camera`: movement toward camera (y coordinate decreases when crossing line)
- `away_from_camera`: movement away from camera (y coordinate increases)

## API Endpoints

### REST API

- `GET /api/stats` - Statistics for the last hour
- `GET /api/events?side=left|right&limit=50` - List of events
- `GET /api/events/{id}` - Event details
- `GET /snapshots/{filename}` - Get snapshot

### WebSocket

- `WS /ws/events` - Real-time events
  - Messages: `{"type": "event_created", "payload": {...}}`

## Privacy & Compliance

⚠️ **IMPORTANT**: The system is designed with privacy in mind:

1. **License plate OCR** - License plates are recognized and stored (with "XXXXX" fallback if recognition fails)
2. **Automatic license plate blurring** - All snapshots automatically blur the license plate area (removed in current version)
3. **Anonymized data** - Only aggregate data and events without identifiers are stored

## Testing

📖 **Detailed guide: [TESTING.md](./TESTING.md)**

To test the system:
1. Get test video (see TESTING.md)
2. Configure `.env` file
3. Calibrate ROI for your video
4. Run the system and verify operation

## Development

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Testing

For testing, use a local video file:

1. Place video file in `backend/test_video.mp4`
2. Set in `.env`: `VIDEO_SOURCE_TYPE=file`
3. Run the system

## Performance

- **CPU**: Works on CPU, expected performance 5-12 FPS
- **GPU** (optional): With CUDA available, YOLOv8 can be accelerated
- **FPS**: Configured via `FPS` in `.env` (recommended: 10)

## Database Structure

SQLite database `traffic_events.db` contains `trafficevent` table:

- `id` - Unique ID
- `ts` - Timestamp
- `side` - Side (left/right)
- `lane` - Lane (1-3)
- `direction` - Direction
- `vehicle_type` - Vehicle type
- `color` - Color
- `make_model` - Make/model
- `make_model_conf` - Confidence
- `snapshot_path` - Path to snapshot (only for left)
- `plate_number` - Recognized license plate number (or "XXXXX")
- `plate_snapshot_path` - Path to license plate snapshot
- `bbox` - Bbox coordinates (JSON)
- `track_id` - Track ID

## Data Cleanup

Events are stored for 24 hours (configurable via `EVENT_TTL_HOURS`). Old records and snapshots are automatically deleted every minute.

## Troubleshooting

### Issue: Video not loading

- Check file path in `.env`
- For YouTube: ensure URL is accessible
- For RTSP/HLS: check stream availability
- For IP cameras: see [IP_CAMERA_SETUP.md](./IP_CAMERA_SETUP.md) for detailed setup guide and troubleshooting

### Issue: No detections

- Check that ROI is configured correctly
- Ensure video contains vehicles
- Check backend logs

### Issue: Incorrect counting

- Recalibrate ROI and counting line
- Check movement direction in config
- Ensure counting lines are positioned correctly

## License

MIT

## Contacts

Project: https://github.com/acid2728k/traffic-hud
