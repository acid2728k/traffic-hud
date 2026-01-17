# ROI Calibration Guide

## What is ROI?

ROI (Region of Interest) - these are areas on video that define:
- Where the road is for each side (left/right)
- Where the counting line passes (when a vehicle crosses this line, it is counted)
- Where the traffic lanes are (1, 2, 3 for each side)

## Step 1: Preparation

1. Start the system with test video file
2. Open video in any video player that shows mouse coordinates
3. Or use annotation tools (LabelImg, CVAT, VGG Image Annotator)

## Step 2: Coordinate Determination

### Left Side (TOWARD CAMERA)

1. **ROI (region of interest)**:
   - Find the area where vehicles moving toward camera are visible
   - Determine 4 polygon points (usually a rectangle)
   - Record coordinates: `[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]`
   - Example for 1920x1080 video: `[[100, 200], [900, 200], [900, 800], [100, 800]]`

2. **Counting Line**:
   - Choose a line that vehicles cross
   - Usually a horizontal line in the middle of ROI
   - Determine start and end points: `[x1, y1]` and `[x2, y2]`
   - Example: `"start": [200, 500], "end": [800, 500]`
   - Direction: `"toward_camera"` (y decreases when moving)

3. **Lanes**:
   - Divide ROI into 3 equal parts by width
   - For each lane, determine 4 polygon points
   - Example for lane 1: `[[100, 200], [366, 200], [366, 800], [100, 800]]`
   - Lane 2: `[[366, 200], [633, 200], [633, 800], [366, 800]]`
   - Lane 3: `[[633, 200], [900, 200], [900, 800], [633, 800]]`

### Right Side (AWAY FROM CAMERA)

Similar to left side, but:
- Direction: `"away_from_camera"` (y increases when moving)
- ROI may be a different area of the screen

## Step 3: Editing roi_config.json

Open file `backend/roi_config.json` and replace coordinates:

```json
{
  "left_side": {
    "name": "LEFT SIDE (TOWARD CAMERA)",
    "direction": "toward_camera",
    "roi": {
      "polygon": [[YOUR_COORDINATES]]
    },
    "counting_line": {
      "start": [YOUR_X1, YOUR_Y1],
      "end": [YOUR_X2, YOUR_Y2],
      "direction": "toward_camera"
    },
    "lanes": [
      {
        "id": 1,
        "polygon": [[LANE_1_COORDINATES]]
      },
      {
        "id": 2,
        "polygon": [[LANE_2_COORDINATES]]
      },
      {
        "id": 3,
        "polygon": [[LANE_3_COORDINATES]]
      }
    ]
  },
  "right_side": {
    // similar
  }
}
```

## Step 4: Verification

1. Restart the system
2. Check backend logs - should see messages about config loading
3. Observe counting in UI
4. If counting is incorrect:
   - Check that counting line is on movement path
   - Ensure direction is correct
   - Check that ROI covers the entire road

## Tips

- **Use annotation tools**: LabelImg, CVAT, VGG Image Annotator will help accurately determine coordinates
- **Test on real video**: Run the system and see if events are detected correctly
- **Start simple**: First configure one side, then the other
- **Check direction**: Ensure movement direction matches settings

## Example Tools

- **LabelImg**: https://github.com/tzutalin/labelImg
- **CVAT**: https://github.com/openvinotoolkit/cvat
- **VGG Image Annotator**: https://www.robots.ox.ac.uk/~vgg/software/via/
