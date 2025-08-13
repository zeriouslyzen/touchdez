# Thesidia Hand Control Alpha

High-performance, local hand gesture recognition for Apple Silicon (macOS). Uses MediaPipe for hand tracking, OpenCV for a minimal on-screen renderer, OSC for external control (e.g., TouchDesigner), and a lightweight web dashboard for monitoring and visuals.

Author: Jack Dangers

## Features
- Real-time hand tracking (MediaPipe Hands)
- Minimal black/white OpenCV overlay with landmarks and a constellation graph
- OSC output for downstream tools (default TouchDesigner on 127.0.0.1:9000)
- Local web dashboard (FastAPI + Canvas) with live gesture, symbol, FPS, and skeleton overlay
- Modular gesture classification with symbolic mappings
- Logs and optional frame capture on gesture change

## Requirements
- macOS on Apple Silicon (M1/M2/M3)
- Homebrew (recommended)
- Python 3.11 (tested)
- Camera permission enabled for the terminal app you use (System Settings → Privacy & Security → Camera)

## Setup
1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -U pip wheel setuptools
pip install -r requirements.txt
```

Notes:
- MediaPipe wheels are available for Python 3.11 on Apple Silicon. If you use a different Python version and encounter errors, switch to 3.11.

## Run
Launch the interface:

```bash
python -m gesture_interface
```

- Press `q` to quit the OpenCV window
- Dashboard: open http://127.0.0.1:8765 for a live HUD and constellation canvas
- Logs: `./logs/gestures.log`
- Frames (on gesture changes): `./frames/`

## Configuration
All runtime options are in `gesture_interface/config/settings.yaml`.

```yaml
camera_index: 0
width: 1280
height: 720
mirror: true
max_num_hands: 1
min_detection_confidence: 0.6
min_tracking_confidence: 0.6
show_camera_background: false
capture_frames_on_change: true
frames_dir: frames
logs_dir: logs
window_title: Thesidia-HandControl-Alpha
black_background: true
draw_fps: true

dashboard:
  enabled: true
  host: 127.0.0.1
  port: 8765

constellation:
  enabled: true
  neighbors: 3
  point_radius: 3
  line_thickness: 1

osc:
  enabled: true
  host: 127.0.0.1
  port: 9000
  send_landmarks: false
  fps_interval_sec: 0.5
```

Key notes:
- Set `mirror: true` for webcam-like behavior
- Set `show_camera_background: true` to render the camera feed as background
- `constellation` controls the extra lines/points overlay
- `osc` enables UDP OSC for external tools
- `dashboard` serves a local monitoring UI

## OSC Interface
Default target: `127.0.0.1:9000`.

Messages:
- `/thesidia/gesture` [string name, string symbol]
- `/thesidia/fps` float
- `/thesidia/hand/0/landmarks` flat array of [x0, y0, z0, x1, y1, z1, ...] when `osc.send_landmarks: true`
- `/thesidia/hand/0/handedness` "Left" or "Right"

Use an OSC In DAT/CHOP (TouchDesigner) or any OSC-capable client to subscribe.

## Dashboard
- URL: http://127.0.0.1:8765
- Shows current gesture, symbol, and FPS
- Renders a constellation field and a white skeleton overlay of the first detected hand

If the dashboard port is in use, adjust `dashboard.port` in the YAML config.

## Troubleshooting
- Camera not opening on macOS: enable Camera permission for your terminal (Terminal, iTerm, or VS Code). If you switch terminals, re-grant permissions.
- MediaPipe installation errors: use Python 3.11 in a fresh venv. Example via Homebrew: `/opt/homebrew/bin/python3.11 -m venv .venv`
- Black screen but app runs: try `show_camera_background: true` to verify input; ensure good lighting and that your hand is within frame.
- Dashboard not updating: refresh the page (hard reload). Ensure port 8765 is free or change it in the config.

## Development
- Code location: `gesture_interface/`
  - `main.py`: program entry, capture loop, wiring
  - `detector.py`: MediaPipe Hands wrapper
  - `renderer.py`: OpenCV overlay
  - `gestures/`: symbolic classification hooks and mappings
  - `osc_output.py`: OSC emitter
  - `dashboard_server.py`, `dashboard_state.py`: web dashboard (FastAPI + Canvas)
- Style: standard Python formatting and type hints where helpful

## Roadmap
- Additional gestures (pinch, swipe, rotate) with temporal smoothing
- Multi-hand support and symmetry-aware symbols
- Configurable gesture-to-command bindings (hotkeys/HID)
- Expanded OSC schema for per-finger dynamics
- Optional TouchDesigner-native modules

## License
MIT (or similar permissive license). Add a LICENSE file as desired.

