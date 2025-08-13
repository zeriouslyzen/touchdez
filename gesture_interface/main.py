import logging
import os
import threading
import time
from datetime import datetime

import cv2
import yaml

from .dashboard_server import run_server
from .dashboard_state import GLOBAL_DASHBOARD_STATE
from .detector import HandLandmarkDetector
from .gestures.symbolic_hooks import GestureClassifier
from .osc_output import OSCEmitter
from .renderer import OverlayRenderer

DEFAULT_CONFIG = {
    "camera_index": 0,
    "width": 1280,
    "height": 720,
    "mirror": True,
    "max_num_hands": 1,
    "min_detection_confidence": 0.6,
    "min_tracking_confidence": 0.6,
    "show_camera_background": False,
    "capture_frames_on_change": True,
    "frames_dir": "frames",
    "logs_dir": "logs",
    "window_title": "Thesidia-HandControl-Alpha",
    "black_background": True,
    "draw_fps": True,
    "dashboard": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 8765,
    },
    "constellation": {
        "enabled": True,
        "neighbors": 3,
        "point_radius": 3,
        "line_thickness": 1,
    },
    "osc": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 9000,
        "send_landmarks": False,
        "fps_interval_sec": 0.5,
    },
}


def ensure_directories(paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def configure_logging(logs_dir: str) -> None:
    ensure_directories([logs_dir])
    log_path = os.path.join(logs_dir, "gestures.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
            # Deep-merge for nested dicts
            base_osc = config["osc"].copy()
            base_osc.update((user_cfg or {}).get("osc", {}))
            base_const = config["constellation"].copy()
            base_const.update((user_cfg or {}).get("constellation", {}))
            base_dash = config["dashboard"].copy()
            base_dash.update((user_cfg or {}).get("dashboard", {}))
            config.update(
                {
                    k: v
                    for k, v in user_cfg.items()
                    if k not in ("osc", "constellation", "dashboard")
                }
            )
            config["osc"] = base_osc
            config["constellation"] = base_const
            config["dashboard"] = base_dash
    return config


def save_frame(frame, frames_dir: str, gesture_name: str) -> None:
    ensure_directories([frames_dir])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{gesture_name}_{timestamp}.jpg"
    cv2.imwrite(os.path.join(frames_dir, filename), frame)


def start_dashboard_server(host: str, port: int) -> None:
    t = threading.Thread(
        target=run_server, kwargs={"host": host, "port": port}, daemon=True
    )
    t.start()


def main() -> None:
    config = load_config()
    configure_logging(config["logs_dir"])  # logs to file and console

    dash_cfg = config.get("dashboard", {})
    if dash_cfg.get("enabled", True):
        start_dashboard_server(
            str(dash_cfg.get("host", "127.0.0.1")), int(dash_cfg.get("port", 8765))
        )

    camera_index = int(config["camera_index"])  # webcam index
    # Prefer AVFoundation on macOS; fallback to default if needed
    backend = cv2.CAP_AVFOUNDATION if hasattr(cv2, "CAP_AVFOUNDATION") else 0
    cap = cv2.VideoCapture(camera_index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logging.error(
            "Could not open webcam at index %s. On macOS, grant Camera access to Terminal/Python in System Settings > Privacy & Security > Camera.",
            camera_index,
        )
        return

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config["height"])

    detector = HandLandmarkDetector(
        max_num_hands=int(config["max_num_hands"]),
        min_detection_confidence=float(config["min_detection_confidence"]),
        min_tracking_confidence=float(config["min_tracking_confidence"]),
    )

    const_cfg = config.get("constellation", {})
    renderer = OverlayRenderer(
        window_title=str(config["window_title"]),
        show_camera_background=bool(config["show_camera_background"]),
        black_background=bool(config["black_background"]),
        draw_fps=bool(config["draw_fps"]),
        mirror=bool(config["mirror"]),
        constellation_enabled=bool(const_cfg.get("enabled", True)),
        constellation_neighbors=int(const_cfg.get("neighbors", 3)),
        constellation_point_radius=int(const_cfg.get("point_radius", 3)),
        constellation_line_thickness=int(const_cfg.get("line_thickness", 1)),
    )

    classifier = GestureClassifier()

    osc_cfg = config.get("osc", {})
    osc_enabled = bool(osc_cfg.get("enabled", False))
    osc = None
    last_osc_fps_time = 0.0
    if osc_enabled:
        osc = OSCEmitter(
            host=str(osc_cfg.get("host", "127.0.0.1")),
            port=int(osc_cfg.get("port", 9000)),
            send_landmarks=bool(osc_cfg.get("send_landmarks", False)),
        )

    last_gesture = None
    last_time = time.time()

    try:
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                logging.warning("Frame grab failed")
                break

            if config["mirror"]:
                frame_bgr = cv2.flip(frame_bgr, 1)

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            hands = detector.process(frame_rgb)
            gesture_name, symbol = classifier.classify(hands)

            now = time.time()
            fps = 1.0 / max(now - last_time, 1e-6)
            last_time = now

            # Prepare normalized landmarks for dashboard (first hand only), preserve last when none
            dash_landmarks = None
            if hands:
                lm, _handed = hands[0]
                dash_landmarks = [(x, y) for (x, y, _z) in lm]

            # Update dashboard state
            GLOBAL_DASHBOARD_STATE.update(gesture_name, symbol, fps, dash_landmarks)

            if osc_enabled and osc:
                # Send FPS at a throttled interval
                if now - last_osc_fps_time >= float(
                    osc_cfg.get("fps_interval_sec", 0.5)
                ):
                    osc.send_fps(fps)
                    last_osc_fps_time = now
                # Optionally send landmarks each frame
                if bool(osc_cfg.get("send_landmarks", False)):
                    osc.send_landmarks(hands)

            output_frame = renderer.render(frame_bgr, hands, gesture_name, symbol, fps)

            # Log and save frame on gesture change
            if gesture_name != last_gesture:
                if gesture_name is not None:
                    logging.info("GESTURE: %s | SYMBOL: %s", gesture_name, symbol)
                    if osc_enabled and osc:
                        osc.send_gesture(gesture_name, symbol)
                    if config["capture_frames_on_change"]:
                        save_frame(output_frame, config["frames_dir"], gesture_name)
                last_gesture = gesture_name

            cv2.imshow(renderer.window_title, output_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
