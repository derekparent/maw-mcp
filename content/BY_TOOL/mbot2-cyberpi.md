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
