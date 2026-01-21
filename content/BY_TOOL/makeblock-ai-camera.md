# Makeblock AI Camera 2.0

Patterns and learnings for using Makeblock AI Camera 2.0 with CyberPi/mBot2.

---

## API Module

**Date:** 2026-01-21
**Project:** sparklebot-mcp

**Context:**
Working with AI Camera 2.0 on CyberPi. Documentation is scattered across help center, lesson files, and forums.

**Learning:**
The camera is accessed via `mbuild.ai_camera` module, NOT `smart_camera`:

```python
import mbuild

# Check current mode
mode = mbuild.ai_camera.ai_camera_func_mode_get(1)
# Returns: 'Face', 'Color', 'Gesture', 'Tag', 'Object', 'Track', 'Posture', 'OCR', 'Speech'

# Switch mode (mode numbers 1-9)
mbuild.ai_camera.ai_camera_set_func_switch(3, 1)  # 3 = Color mode
```

**Mode Numbers:**
| # | Mode | Mode String |
|---|------|-------------|
| 1 | Face | 'Face' |
| 2 | Object | 'Object' |
| 3 | Color | 'Color' |
| 4 | Tag | 'Tag' |
| 5 | Gesture | 'Gesture' |
| 6 | Line/Path | 'Track' |
| 7 | Posture | 'Posture' |
| 8 | OCR | 'OCR' |
| 9 | Speech | 'Speech' |

**Why it matters:**
Online docs mention `smart_camera` but the actual mBlock-generated code uses `mbuild.ai_camera`.

---

## Color Mode Position Data

**Date:** 2026-01-21
**Project:** sparklebot-mcp

**Context:**
Needed to track colored objects for robot following behavior.

**Learning:**
Color mode provides X, Y, Width, Height via attribute parameter:

```python
# Attribute: 1=X, 2=Y, 3=Width, 4=Height
x = mbuild.ai_camera.ai_camera_color_spatial_attribute_get(1, 1, 1)  # X position
y = mbuild.ai_camera.ai_camera_color_spatial_attribute_get(1, 2, 1)  # Y position
w = mbuild.ai_camera.ai_camera_color_spatial_attribute_get(1, 3, 1)  # Width
h = mbuild.ai_camera.ai_camera_color_spatial_attribute_get(1, 4, 1)  # Height
# Returns -1 if not detected
```

**Position interpretation:**
- Resolution: 640x480 pixels
- X < 280 → target on LEFT
- X > 360 → target on RIGHT
- X 280-360 → target CENTERED
- Width as distance proxy: larger = closer

**Why it matters:**
This enables "follow the ball" without ultrasonic sensor.

---

## AprilTags for Navigation

**Date:** 2026-01-21
**Project:** sparklebot-mcp

**Context:**
Ultrasonic sensor doesn't physically fit when camera is attached. Needed alternative navigation.

**Learning:**
AprilTags provide DISTANCE and ROTATION ANGLE - better than ultrasonic for targeted navigation:

```python
mbuild.ai_camera.ai_camera_set_func_switch(4, 1)  # Tag mode
mbuild.ai_camera.ai_camera_tag_func_mode_set(3, 1)  # AprilTag sub-mode

# Get tag analysis results
result = mbuild.ai_camera.ai_camera_tag_analysis_result_get(attr, 1)
```

**Why it matters:**
AprilTags can replace ultrasonic for waypoint navigation with more precision (actual distance + angle vs just distance).

---

## Width as Distance Proxy

**Date:** 2026-01-21
**Project:** sparklebot-mcp

**Context:**
Camera provides no direct distance measurement except AprilTags.

**Learning:**
Use detected object WIDTH as a distance proxy:

```python
width = mbuild.ai_camera.ai_camera_color_spatial_attribute_get(1, 3, 1)

if width > 180:
    # Object is CLOSE - stop or slow down
    speed = 0
elif width > 0:
    # Object detected at distance - approach
    # Speed proportional to distance (larger width = slower)
    speed = (180 - width) / 2.5
else:
    # Not detected
    speed = 0
```

**Why it matters:**
Enables approach/distance control for any detected object (color, face, person) without ultrasonic.

---

## Ground Truth: Lesson Files

**Date:** 2026-01-21
**Project:** sparklebot-mcp

**Context:**
API documentation is inconsistent across sources. ChatGPT/Perplexity give plausible but wrong APIs.

**Learning:**
Makeblock's mBlock lesson files (.mblock → .md exports) contain the VERIFIED working API calls:

- Lesson files have block-to-Python conversions
- These are the actual APIs that run on hardware
- Example: `ai_camera_color_spatial_attribute_get()` not `color_get_info()`

**Research pattern:**
1. Find official Makeblock lesson PDFs
2. Extract Python code from lesson files
3. Trust lesson code over documentation
4. Test on hardware to confirm

**Why it matters:**
Hours of debugging avoided by using lesson code as ground truth instead of documentation.
