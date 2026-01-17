# Traffic HUD Quick Start

## Step 1: Environment Setup

```bash
cd backend
cp .env.example .env
# Edit .env if needed
```

## Step 2: Get Test Video

### Option A: Use Existing Video

Place video file in `backend/test_video.mp4`:

```bash
cp /path/to/your/video.mp4 backend/test_video.mp4
```

### Option B: Download Test Video

```bash
cd backend
./download_test_video.sh
```

### Option C: Use YouTube Live

In `backend/.env` set:

```env
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI
```

## Step 3: ROI Calibration (Optional)

If using your own video, open `backend/roi_config.json` and configure coordinates for your video.

See [CALIBRATION.md](./CALIBRATION.md) for detailed instructions.

## Step 4: Launch

```bash
# From project root directory
docker compose up --build
```

## Step 5: Open in Browser

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Parameter Configuration

Edit `backend/.env`:

```env
# Processing FPS (recommended 10 for CPU, can increase to 15)
FPS=10

# Detection confidence threshold (0.15-0.5, lower = more detections)
CONFIDENCE_THRESHOLD=0.25

# Event TTL in hours (how long to store events)
EVENT_TTL_HOURS=24
```

## Verification

1. Open http://localhost:3000
2. Check status: should be "STREAM: LIVE"
3. Observe events in panels
4. Click on event to view details

## Troubleshooting

### Video not loading

```bash
# Check file path
ls -la backend/test_video.mp4

# Check logs
docker compose logs backend
```

### No detections

1. Ensure ROI is configured correctly
2. Try lowering `CONFIDENCE_THRESHOLD` to 0.15
3. Check that video contains vehicles

### Incorrect counting

1. Recalibrate ROI (see CALIBRATION.md)
2. Check movement direction in roi_config.json
3. Ensure counting line is on movement path

## Additional Documentation

- [README.md](./README.md) - Full documentation
- [CALIBRATION.md](./CALIBRATION.md) - ROI calibration
- [TESTING.md](./TESTING.md) - Detailed testing guide
