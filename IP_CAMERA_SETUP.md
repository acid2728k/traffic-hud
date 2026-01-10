# IP Camera Setup Guide

This guide will help you connect an IP camera as a video source for the Traffic HUD machine vision system.

## Table of Contents
1. [IP Camera Preparation](#ip-camera-preparation)
2. [Obtaining RTSP URL](#obtaining-rtsp-url)
3. [System Configuration](#system-configuration)
4. [Examples for Different Manufacturers](#examples-for-different-manufacturers)
5. [Connection Verification](#connection-verification)
6. [Troubleshooting](#troubleshooting)

---

## IP Camera Preparation

### Step 1: Connecting Camera to Network

1. **Physical Connection:**
   - Connect the camera to the router via Ethernet cable (recommended)
   - Or connect the camera to Wi-Fi network (if supported)

2. **Network Configuration:**
   - Ensure the camera and Traffic HUD server are on the same network
   - Note the camera's IP address (can be found in router settings or through the manufacturer's mobile app)

3. **Availability Check:**
   ```bash
   ping <CAMERA_IP_ADDRESS>
   ```
   Example: `ping 192.168.1.100`

### Step 2: Camera Configuration

1. **Access Camera Web Interface:**
   - Open a browser
   - Navigate to: `http://<CAMERA_IP_ADDRESS>`
   - Login with username and password (usually admin/admin or as specified in the manual)

2. **Enable RTSP Stream:**
   - Find Settings → Network → RTSP section
   - Enable RTSP server
   - Note the RTSP port (usually 554)
   - Note the stream path (usually `/stream1` or `/h264`)

---

## Obtaining RTSP URL

RTSP URL follows this format:

```
rtsp://[username]:[password]@[IP_address]:[port]/[path]
```

### RTSP URL Examples:

**Basic Format:**
```
rtsp://admin:admin123@192.168.1.100:554/stream1
```

**Without Authentication (not recommended):**
```
rtsp://192.168.1.100:554/stream1
```

**With Codec Specification:**
```
rtsp://admin:admin123@192.168.1.100:554/h264
```

---

## System Configuration

### Method 1: Using .env File (Recommended)

1. **Create `.env` file in `backend/` directory:**
   ```bash
   cd backend
   touch .env
   ```

2. **Add the following lines to `.env` file:**
   ```env
   VIDEO_SOURCE_TYPE=rtsp_url
   VIDEO_SOURCE_URL=rtsp://admin:admin123@192.168.1.100:554/stream1
   FPS=10
   ```

   **Replace:**
   - `admin:admin123` with your camera's username and password
   - `192.168.1.100` with your camera's IP address
   - `554` with RTSP port (if different)
   - `/stream1` with your camera's stream path

3. **Restart Backend:**
   ```bash
   # Stop current process
   lsof -ti:8000 | xargs kill -9
   
   # Start again
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Method 2: Using Environment Variables

```bash
export VIDEO_SOURCE_TYPE=rtsp_url
export VIDEO_SOURCE_URL=rtsp://admin:admin123@192.168.1.100:554/stream1
export FPS=10

cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Direct config.py Editing (Not Recommended)

If you need to change settings directly in code, edit `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    video_source_type: str = "rtsp_url"  # Change to rtsp_url
    video_source_url: Optional[str] = "rtsp://admin:admin123@192.168.1.100:554/stream1"
    # ...
```

---

## Examples for Different Manufacturers

### Hikvision

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]:554/Streaming/Channels/[channel]
```

**Examples:**
```
# Main stream (high quality)
rtsp://admin:admin123@192.168.1.100:554/Streaming/Channels/101

# Sub stream (low quality)
rtsp://admin:admin123@192.168.1.100:554/Streaming/Channels/102
```

**Configuration:**
- Access web interface: `http://192.168.1.100`
- Settings → Network → Advanced Settings → RTSP
- Ensure RTSP is enabled

### Dahua

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]:554/cam/realmonitor?channel=1&subtype=0
```

**Examples:**
```
# Main stream
rtsp://admin:admin123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0

# Sub stream
rtsp://admin:admin123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=1
```

### TP-Link

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]:554/stream1
```

**Example:**
```
rtsp://admin:admin123@192.168.1.100:554/stream1
```

### Reolink

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]:554/h264Preview_01_main
```

**Example:**
```
rtsp://admin:admin123@192.168.1.100:554/h264Preview_01_main
```

### Axis

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]/axis-media/media.amp
```

**Example:**
```
rtsp://root:pass@192.168.1.100/axis-media/media.amp
```

### Foscam

**RTSP URL Format:**
```
rtsp://[username]:[password]@[IP]:554/videoMain
```

**Example:**
```
rtsp://admin:admin123@192.168.1.100:554/videoMain
```

### Generic Cameras (ONVIF)

If your camera supports ONVIF, you can use ONVIF Device Manager to find the RTSP URL:

1. Download ONVIF Device Manager: https://sourceforge.net/projects/onvifdm/
2. Launch and find your camera
3. Navigate to "Live Video" section
4. Copy the RTSP URL

---

## Connection Verification

### Step 1: RTSP Stream Verification

Use VLC Media Player for verification:

1. **Install VLC** (if not already installed): https://www.videolan.org/

2. **Open Stream:**
   - VLC → Media → Open Network Stream
   - Enter RTSP URL: `rtsp://admin:admin123@192.168.1.100:554/stream1`
   - Click "Play"

3. **If video plays** - camera is configured correctly ✅

### Step 2: Command Line Verification

Use `ffmpeg` for verification:

```bash
ffmpeg -rtsp_transport tcp -i rtsp://admin:admin123@192.168.1.100:554/stream1 -frames:v 1 test_frame.jpg
```

If the command executed without errors and `test_frame.jpg` was created - stream is working ✅

### Step 3: Traffic HUD System Verification

1. **Start backend** with RTSP settings
2. **Check logs:**
   ```bash
   tail -f backend.log
   ```

3. **Expected Messages:**
   ```
   INFO:app.services.ingest:Opening RTSP stream: rtsp://...
   INFO:app.services.ingest:RTSP stream opened successfully
   INFO:app.main:Video ingest initialized successfully
   ```

4. **Open frontend** in browser: `http://localhost:3000`
5. **Verify that video is streaming**

---

## Troubleshooting

### Issue 1: "Failed to open RTSP stream"

**Possible Causes:**
- Incorrect RTSP URL
- Wrong username/password
- Camera not accessible on network
- RTSP disabled on camera

**Solutions:**
1. Verify RTSP URL in VLC
2. Ensure username and password are correct
3. Check camera availability: `ping <IP_address>`
4. Enable RTSP in camera settings

### Issue 2: "Connection timeout"

**Possible Causes:**
- Camera and server on different networks
- Firewall blocking connection
- Incorrect port

**Solutions:**
1. Ensure camera and server are on the same network
2. Check firewall settings
3. Verify RTSP port (usually 554)

### Issue 3: Video Not Playing

**Possible Causes:**
- Unsupported codec
- Resolution too high
- Network bandwidth issues

**Solutions:**
1. Use sub stream (lower resolution)
2. Reduce resolution in camera settings
3. Check network speed

### Issue 4: Frequent Connection Drops

**Possible Causes:**
- Unstable network connection
- Network congestion
- Camera issues

**Solutions:**
1. Use Ethernet instead of Wi-Fi
2. Reduce FPS in settings: `FPS=5` or `FPS=10`
3. Use TCP instead of UDP (if supported):
   ```python
   # ingest.py already uses OpenCV, which defaults to TCP
   ```

### Issue 5: "Permission denied" or Authentication Errors

**Solutions:**
1. Check username and password
2. Ensure user has permissions to view RTSP stream
3. Try creating a new user in camera settings with viewing permissions

### Issue 6: Slow Frame Processing

**Solutions:**
1. Reduce FPS: `FPS=5` in `.env`
2. Use sub stream (lower resolution)
3. Reduce camera resolution in settings

---

## Additional Settings

### FPS Configuration (Frames Per Second)

In `.env` file:
```env
FPS=10  # Recommended 5-15 for IP cameras
```

**Recommendations:**
- **5 FPS** - for slow traffic, resource saving
- **10 FPS** - optimal for most cases
- **15 FPS** - for fast traffic, requires more resources

### Using TCP Instead of UDP

OpenCV defaults to TCP for RTSP, which is more reliable but may be slower.

If you need to use UDP (faster but less reliable), you can use `ffmpeg`:

1. Install `ffmpeg`: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)

2. Use pipe:
   ```python
   # This requires code changes in ingest.py
   # Refer to OpenCV documentation for configuration
   ```

### Resolution Settings

For best performance, it's recommended to use **1280x720 (720p)** or **1920x1080 (1080p)** resolution.

Configure resolution in camera web interface:
- Settings → Video → Resolution → 1280x720 or 1920x1080

---

## Security

### Security Recommendations:

1. **Change default password** on camera
2. **Use strong password** (minimum 12 characters, letters, numbers, symbols)
3. **Restrict access** to RTSP stream only from server IP address (if supported)
4. **Use VPN** for accessing camera from outside network
5. **Regularly update camera firmware**

### Credential Storage:

**DO NOT store passwords in code!** Use `.env` file and add it to `.gitignore`:

```bash
# In .gitignore
.env
```

---

## Configuration Examples

### Example 1: Hikvision Camera

```env
VIDEO_SOURCE_TYPE=rtsp_url
VIDEO_SOURCE_URL=rtsp://admin:MySecurePass123@192.168.1.100:554/Streaming/Channels/101
FPS=10
```

### Example 2: Dahua Camera

```env
VIDEO_SOURCE_TYPE=rtsp_url
VIDEO_SOURCE_URL=rtsp://admin:MySecurePass123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0
FPS=10
```

### Example 3: Camera with Token Authentication

Some cameras require a token instead of password. In this case, the URL may look like:
```
rtsp://admin@192.168.1.100:554/stream1?token=abc123def456
```

---

## Support

If you encounter issues:

1. Check backend logs: `tail -f backend.log`
2. Check your camera documentation
3. Ensure camera supports RTSP
4. Try connecting through VLC for diagnostics

---

## Useful Links

- [RTSP Protocol Specification](https://tools.ietf.org/html/rfc2326)
- [ONVIF Device Manager](https://sourceforge.net/projects/onvifdm/)
- [VLC Media Player](https://www.videolan.org/)
- [OpenCV VideoCapture Documentation](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)

---

**Last Updated:** 2025-01-10
