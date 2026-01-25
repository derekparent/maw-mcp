# macOS Virtualization

Patterns and limitations for running VMs on macOS (Apple Silicon).

---

## USB 3.0 Passthrough Limitation

**Date:** 2026-01-24
**Project:** Azure Kinect setup
**Context:** Attempting to use high-bandwidth USB devices (Azure Kinect) in Linux VMs on macOS

### Problem

USB devices requiring USB 3.0 bandwidth (5Gbps) cannot function properly in macOS VMs. The devices appear visible but connect at USB 2.0 speeds (480Mbps), causing I/O errors.

### Affected Virtualizers

| Virtualizer | Backend | USB Passthrough |
|-------------|---------|-----------------|
| OrbStack | Virtualization.framework | ❌ None at all |
| UTM | QEMU | ⚠️ USB 2.0 only |
| Parallels | Proprietary | ? (untested, may work) |

### Symptoms

```
lsusb -t
# Device shows on 480M bus instead of 5000M bus

# SDK/libusb errors:
LIBUSB_ERROR_IO
submiturb failed error -1 errno=2
```

### Root Cause

- **OrbStack**: Uses Apple's Virtualization.framework which doesn't support USB passthrough
- **UTM/QEMU**: USB passthrough works but macOS limits it to USB 2.0 speeds

### Workarounds

1. **Native Linux** - Dual boot or dedicated Linux machine
2. **Parallels Desktop** - Commercial option, may have better USB 3.0 support
3. **Remote Linux box** - Raspberry Pi or mini PC with the USB device
4. **Accept limitation** - Wait for better macOS virtualization support

### Devices Known Affected

- Azure Kinect DK (requires USB 3.0 for depth streaming)
- Other high-bandwidth USB cameras
- USB 3.0 capture cards
- Any device requiring isochronous USB 3.0 transfers

### Prevention

Before attempting USB passthrough on macOS:
1. Check if device requires USB 3.0 bandwidth
2. If yes, plan for native Linux from the start
3. VM approach only works for USB 2.0 devices

---
