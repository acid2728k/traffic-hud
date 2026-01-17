# Traffic HUD Testing Guide

## Test Video Preparation

### Option 1: Use Existing Video

Place a video file with traffic in `backend/test_video.mp4`:

```bash
# Example: copy existing video
cp /path/to/your/traffic_video.mp4 backend/test_video.mp4
```

### Option 2: Download from YouTube

Use the script (requires yt-dlp):

```bash
cd backend
./download_test_video.sh
```

Or manually:

```bash
cd backend
yt-dlp -f "best[ext=mp4]" "YOUTUBE_URL" -o test_video.mp4
```

### Option 3: Use YouTube Live

In `.env` set:

```env
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI
```

## .env Configuration

1. Open `backend/.env`:

```bash
cd backend
nano .env  # or use any editor
```

2. Configure parameters:

```env
# For local file
VIDEO_SOURCE_TYPE=file
VIDEO_SOURCE_FILE=./test_video.mp4

# Processing FPS (recommended 10 for CPU)
FPS=10

# Detection confidence threshold (0.0-1.0, higher = stricter)
CONFIDENCE_THRESHOLD=0.25

# Event TTL in hours
EVENT_TTL_HOURS=24
```

## ROI Calibration

1. **Start the system** (see below)
2. **Open video** in video player with mouse coordinates
3. **Determine coordinates**:
   - Road areas (ROI)
   - Counting lines
   - Traffic lanes
4. **Edit** `backend/roi_config.json`
5. **Restart** the system

For details: see [CALIBRATION.md](./CALIBRATION.md)

## Starting Tests

### Via Docker (recommended)

```bash
# From project root directory
docker compose up --build

# In another terminal check logs
docker compose logs -f backend
```

### Locally (for development)

#### Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Ensure .env is configured
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Verification

1. **Open browser**: http://localhost:3000
2. **Check status**: Should be "STREAM: LIVE"
3. **Observe events**: Should appear in left/right panels
4. **Check statistics**: "Last 60 min" should update
5. **Open details**: Click on event to view details

## API Testing

```bash
# Statistics
curl http://localhost:8000/api/stats

# Events
curl http://localhost:8000/api/events?side=left&limit=10

# Event details
curl http://localhost:8000/api/events/1
```

## Debugging

### Issue: No detections

1. Check backend logs:
   ```bash
   docker compose logs backend
   ```

2. Ensure that:
   - Video is loading (check path in .env)
   - ROI is configured correctly
   - CONFIDENCE_THRESHOLD is not too high

3. Try lowering threshold:
   ```env
   CONFIDENCE_THRESHOLD=0.15
   ```

### Issue: Incorrect counting

1. Check `roi_config.json`:
   - Coordinates match video resolution
   - Counting line is on movement path
   - Direction is correct (toward_camera/away_from_camera)

2. Visualize ROI (can add debug mode)

### Issue: Video not loading

1. Check file path:
   ```bash
   ls -la backend/test_video.mp4
   ```

2. For YouTube: ensure URL is accessible

3. Check format: supported formats are mp4, avi, mov, mkv

## Test Scenarios

### 1. Basic Test

- ✅ System starts
- ✅ Video loads
- ✅ Detections work
- ✅ Events are created
- ✅ UI updates

### 2. Counting Test

- ✅ Events created when crossing line
- ✅ Correct side (left/right)
- ✅ Correct lane (1/2/3)
- ✅ Statistics update

### 3. Snapshots Test

- ✅ Snapshots created for left side
- ✅ License plates recognized (or "XXXXX" if not)
- ✅ Snapshots displayed in UI
- ✅ Modal opens with details

### 4. Real-time Test

- ✅ WebSocket connection
- ✅ Events arrive in real-time
- ✅ Fallback to polling when WS disconnected

## Performance

Expected metrics on CPU:

- **Processing FPS**: 5-12 FPS (depends on CPU)
- **Detection latency**: 100-300ms per frame
- **Memory**: ~500MB-1GB (depends on YOLO model)

To improve performance:

- Use GPU (CUDA) for YOLOv8
- Reduce FPS in .env
- Use smaller YOLO model (yolov8n.pt is already the smallest)

## Next Steps After Testing

1. ✅ Calibrate ROI for your video
2. ✅ Configure FPS and thresholds
3. ✅ Test on real stream
4. ✅ Monitor performance
5. ✅ Configure data cleanup (TTL)
