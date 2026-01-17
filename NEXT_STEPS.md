# What's Next? 🚀

## ✅ Project is Ready to Launch!

All files are created, configuration is set up. Now you can run the system.

## 📝 Step-by-Step Action Plan

### Step 1: Get Test Video (5 minutes)

**Option A: Use existing video**
```bash
# Place your video file in backend/
cp /path/to/your/traffic_video.mp4 backend/test_video.mp4
```

**Option B: Download test video**
```bash
cd backend
./download_test_video.sh
```

**Option C: Use YouTube Live**
Edit `backend/.env`:
```env
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=H0Z6faxNLCI
```

### Step 2: Start System (2 minutes)

```bash
# From project root directory
docker compose up --build
```

This will take several minutes on first run (downloading images, installing dependencies).

### Step 3: Open in Browser

- **Frontend (HUD interface)**: http://localhost:3000
- **API documentation**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Step 4: Verify Operation

1. ✅ Check status: should be "STREAM: LIVE"
2. ✅ Observe events in panels (left/right side)
3. ✅ Click on event to view details
4. ✅ Check "Last 60 min" statistics

### Step 5: ROI Calibration (if needed)

If counting is incorrect or no detections:

1. Open `backend/roi_config.json`
2. Configure coordinates for your video
3. See [CALIBRATION.md](./CALIBRATION.md) for details
4. Restart: `docker compose restart backend`

## 🔧 Parameter Configuration

### Change Processing FPS

In `backend/.env`:
```env
FPS=10  # Can be increased to 15 for more powerful CPU
```

### Change Detection Threshold

In `backend/.env`:
```env
CONFIDENCE_THRESHOLD=0.25  # Lower to 0.15 for more detections
```

### Change Video Source

In `backend/.env`:
```env
# Local file
VIDEO_SOURCE_TYPE=file
VIDEO_SOURCE_FILE=./test_video.mp4

# YouTube Live
VIDEO_SOURCE_TYPE=youtube_url
YOUTUBE_URL=https://www.youtube.com/watch?v=...

# HLS stream
VIDEO_SOURCE_TYPE=hls_url
VIDEO_SOURCE_URL=https://example.com/stream.m3u8

# RTSP stream
VIDEO_SOURCE_TYPE=rtsp_url
VIDEO_SOURCE_URL=rtsp://example.com/stream
```

## 📚 Useful Commands

### View Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop System
```bash
docker compose down
```

### Restart After Changes
```bash
docker compose restart backend
```

### Full Rebuild
```bash
docker compose down
docker compose up --build
```

## 🐛 Troubleshooting

### Issue: Video not loading
```bash
# Check file path
ls -la backend/test_video.mp4

# Check logs
docker compose logs backend | grep -i error
```

### Issue: No detections
1. Ensure ROI is configured correctly
2. Try lowering `CONFIDENCE_THRESHOLD` to 0.15
3. Check that video contains vehicles

### Issue: Incorrect counting
1. Recalibrate ROI (see CALIBRATION.md)
2. Check movement direction in roi_config.json
3. Ensure counting line is on movement path

## 📖 Documentation

- **[README.md](./README.md)** - Full project documentation
- **[QUICK_START.md](./QUICK_START.md)** - Quick start
- **[TESTING.md](./TESTING.md)** - Detailed testing guide
- **[CALIBRATION.md](./CALIBRATION.md)** - ROI calibration

## 🎯 What's Next After Launch?

1. **Testing**: Test operation on different videos
2. **Calibration**: Configure ROI for your specific video
3. **Optimization**: Configure FPS and thresholds for your hardware
4. **Monitoring**: Monitor performance
5. **Improvements**: Add your features (if needed)

## 💡 Tips

- Start with local video file for testing
- Use short videos (1-2 minutes) for quick verification
- Calibrate ROI gradually: first one side, then the other
- Save working ROI configurations for different cameras

---

**Ready to start?** Run `docker compose up --build` and open http://localhost:3000! 🚀
