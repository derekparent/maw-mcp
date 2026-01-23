# mBot2 / CyberPi (Makeblock)

Patterns and gotchas for Makeblock mBot2 robot with CyberPi brain, programmed via mBlock IDE.

---

## Upload Mode vs Live Mode

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
mBlock has two execution modes:
- **Live Mode** (green flag): Runs while connected via USB, has more APIs available
- **Upload Mode**: Flashes code to CyberPi memory for standalone operation

**Gotcha:**
`cyberpi.audio.play_say()` (text-to-speech) does **NOT exist** in Upload Mode MicroPython. The function is only available in Live Mode.

```python
# This FAILS in Upload Mode:
cyberpi.audio.play_say("Hello")  # AttributeError - function doesn't exist

# Verify with:
hasattr(cyberpi.audio, "play_say")  # Returns False in Upload Mode
```

**Solution:**
Use `cyberpi.audio.play_tone(frequency, duration)` to create "robot speech" patterns instead:

```python
def robot_chirp(freq, dur):
    try:
        cyberpi.audio.play_tone(freq, dur)
    except Exception:
        pass

# Vary frequency and duration for "speech cadence"
robot_chirp(860, 0.05)  # High chirp
robot_chirp(740, 0.07)  # Lower chirp
```

---

## Time Module

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
Need to use `time.sleep()` and `time.time()` in CyberPi Python.

**Gotcha:**
Use the standard Python `time` module, NOT `cyberpi.time`:

```python
# CORRECT:
import time
time.sleep(0.5)
now = time.time()

# WRONG (may cause errors):
cyberpi.time.sleep(0.5)  # Don't use this
```

---

## Safe Sensor Wrappers

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi sensors (ultrasonic, light, loudness) can throw exceptions if hardware isn't connected or port is wrong.

**Problem:**
Unhandled sensor errors crash the entire program.

**Solution:**
Wrap ALL sensor calls in try/except with safe fallbacks:

```python
def get_distance_cm():
    """Returns distance or 999 (far) if sensor fails."""
    try:
        return mbot2.ultrasonic2.get(1)
    except Exception:
        pass
    try:
        return mbot2.ultrasonic2.get(2)  # Try other port
    except Exception:
        pass
    return 999  # Safe fallback - "nothing nearby"

def get_loudness_value():
    """Returns loudness or 0 if sensor fails."""
    try:
        return cyberpi.get_loudness("maximum")
    except Exception:
        try:
            return cyberpi.loudness()
        except Exception:
            return 0

def get_brightness_value():
    """Returns brightness or 100 (bright) if sensor fails."""
    try:
        return cyberpi.get_bri()
    except Exception:
        try:
            return cyberpi.light()
        except Exception:
            return 100
```

---

## Memory Limitations

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi runs MicroPython with limited memory.

**Gotcha:**
Large string arrays defined at module level can cause errors:

```python
# May fail with memory issues:
jokes = [
    "Very long joke string 1...",
    "Very long joke string 2...",
    # ... 20+ long strings
]
```

**Solution:**
- Keep string lists shorter (8-10 items max)
- Use shorter strings when possible
- Consider loading strings on-demand if needed

---

## Code Indentation in mBlock

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
Pasting Python code into mBlock IDE.

**Gotcha:**
Leading spaces on line 1 cause `IndentationError`:

```python
# WRONG (spaces before import):
  import cyberpi  # Error on line 1!

# CORRECT (no leading spaces):
import cyberpi  # Works
```

**Prevention:**
When pasting code, ensure line 1 starts at column 0 with no leading whitespace.

---

## LED Functions

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi has onboard RGB LEDs.

**Pattern:**
```python
# Set all LEDs to color (R, G, B values 0-255)
cyberpi.led.on(255, 100, 200)  # Pink

# Turn off
cyberpi.led.off()

# Wrap in try/except for safety
def safe_led(r, g, b):
    try:
        cyberpi.led.on(r, g, b)
    except Exception:
        pass
```

---

## Button Detection

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi has A, B, and middle buttons.

**Pattern:**
```python
# Check if button is currently pressed
cyberpi.controller.is_press("a")  # Returns True/False
cyberpi.controller.is_press("b")
cyberpi.controller.is_press("middle")

# For toggle behavior, use latching:
button_a_latch = False

while True:
    a_now = cyberpi.controller.is_press("a")
    if a_now and not button_a_latch:
        button_a_latch = True
        # Do action here (only fires once per press)
    elif not a_now:
        button_a_latch = False
```

---

## Motion Sensors

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi has accelerometer for detecting shake, tilt, etc.

**Pattern:**
```python
# Shake detection
if cyberpi.is_shake():
    # Robot is being shaken

# Tilt detection
if cyberpi.is_tiltback():
    # Tilted backward (picked up)
if cyberpi.is_tiltforward():
    # Tilted forward (set down)
```

---

## Motor Control

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
mBot2 has two drive motors.

**Pattern:**
```python
# Drive with power levels (-100 to 100)
mbot2.drive_power(left_power, right_power)

# Forward
mbot2.drive_power(40, 40)

# Backward
mbot2.drive_power(-30, -30)

# Spin right
mbot2.drive_power(50, -50)

# Spin left
mbot2.drive_power(-50, 50)

# Stop
mbot2.drive_power(0, 0)
```

---

## Built-in Sounds

**Date:** 2026-01-18
**Project:** SparkleBot

**Context:**
CyberPi has built-in music/sounds.

**Pattern:**
```python
# Play built-in music
cyberpi.audio.play_music("birthday", 1)  # Play once

# Other options: "entertainer", "chase", "correct"

# Set volume (0-100)
cyberpi.audio.set_vol(100)

# Play tone (frequency Hz, duration seconds)
cyberpi.audio.play_tone(880, 0.1)  # A5 note, 100ms
```

---

## Network Debugging Pattern: IP Consistency

**Date:** 2026-01-21
**Project:** SparkleBot MCP

**Context:**
When robot shows `EHOSTUNREACH` or can't connect to MQTT broker, the issue is often IP mismatch across configs.

**Problem:**
Robot connected to WiFi but couldn't reach Mac's MQTT broker. IPs were inconsistent:
- Mac actual: `192.168.0.167`
- config.yaml: `192.168.0.50`
- robot/main.py: `192.168.1.100`

**Solution:**
Check ALL IP references before testing:
```bash
# 1. Find Mac's actual IP
ipconfig getifaddr en0   # or: ip route get 1 | awk '{print $7}'

# 2. Check all config files
grep -r "192.168" config.yaml robot/main.py

# 3. Ensure they match
```

**Prevention:**
- Keep IPs in a single source (config.yaml)
- Document which IP goes where
- After network changes, verify IP and update configs

---

## Guest Networks and Local Access

**Date:** 2026-01-21
**Project:** SparkleBot MCP

**Context:**
Mac and robot both on guest network, robot couldn't reach Mac.

**Gotcha:**
Guest networks with "Allow Local Access" enabled CAN reach devices on the main network, but not necessarily each other depending on AP isolation settings.

**Solution:**
For MQTT/robotics projects, prefer having both devices on the main network to avoid AP isolation issues entirely.

---

## MCP + MQTT Architecture: Natural Language Hardware Control

**Date:** 2026-01-21
**Project:** SparkleBot MCP

**Context:**
Successfully demonstrated natural language control of physical robot via MCP.

**Pattern:**
```
User (natural language) → Claude (interprets intent)
    → MCP tools (translate to protocol)
    → MQTT (transport)
    → Robot (dumb executor)
```

**Key Insight:**
Claude doesn't need pre-scripted commands. When given "make it do a little dance", Claude choreographs by calling available MCP tools in sequence (turns, LEDs, sounds) to achieve the intent.

**Enabling Factors:**
1. MCP tools have clear docstrings explaining what they do
2. Robot executor responds to discrete commands
3. Claude has context about available capabilities

---

## Ultrasonic Sensor: Default Value is Max Range

**Date:** 2026-01-21
**Project:** SparkleBot MCP

**Context:**
Testing ultrasonic distance sensor, initially got 300cm readings.

**Gotcha:**
When nothing is in range, `mbuild.ultrasonic2.get()` returns 300 (max range), not 0 or error.

**Pattern:**
```python
dist = mbuild.ultrasonic2.get()
if dist >= 300:
    # Nothing detected in range
elif dist < 20:
    # Object very close
```

**Note:** Verified sensor works by placing hand in front - got accurate 5-7cm readings.

---

## CLI Upload: Bypass mBlock GUI with mpremote

**Date:** 2026-01-22
**Project:** SparkleBot MCP

**Context:**
mBlock GUI upload is slow iteration bottleneck. Each debug cycle: edit in Cursor → manual upload in mBlock → test → report back.

**Key Finding:**
mBlock "Upload Mode" is just standard MicroPython Raw REPL protocol (`Ctrl+C → Ctrl+A → write file → Ctrl+D`). The protocol is NOT proprietary.

**Solution:**
Use `mpremote` (official MicroPython CLI tool):

```bash
# Install
pip install mpremote

# Close mBlock completely first (mLink holds serial port!)

# Find device
mpremote connect list

# Upload
mpremote cp robot/main.py :/main.py

# Run immediately (optional)
mpremote run robot/main.py
```

**Wrapper script for Cursor:**
```bash
#!/bin/bash
# deploy.sh
mpremote cp robot/main.py :/main.py && echo "✓ Uploaded"
```

**Critical Prerequisite:**
Close mBlock and mLink completely. Check Activity Monitor if "device busy" error.

**Alternative Tools:**
- `ampy` (Adafruit) - older, works
- `rshell` - more powerful, can be finicky
- Thonny IDE - GUI but file browser useful

**Source:**
CyberPi uses ESP32-WROVER-B with USB-to-UART bridge (CH340/CP210x). No native USB mass storage (hardware limitation), but serial REPL works.

---

## MicroPython API Returns Strings, Not Ints

**Date:** 2026-01-22
**Project:** SparkleBot MCP

**Context:**
AprilTag navigation demo failing silently. Comparisons like `v2 > 0` always evaluated False.

**Problem:**
`ai_camera_tag_analysis_result_get()` returns strings, not integers:

```python
# FAILS:
v2 = cam.ai_camera_tag_analysis_result_get(2, 1)
if v2 > 0:  # Always False because "5" > 0 is type error in MicroPython
```

**Solution:**
Cast ALL camera API returns immediately:

```python
# CORRECT:
v2 = int(cam.ai_camera_tag_analysis_result_get(2, 1))
if v2 > 0:  # Now works
```

**Prevention:**
- Add `int()` cast at API boundary for ALL numeric camera values
- Use debug prints to verify types: `console.println("v2 type: %s" % type(v2))`
- MicroPython type coercion differs from Python 3
