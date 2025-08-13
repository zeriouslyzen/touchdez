from typing import List, Optional, Tuple

import cv2
import numpy as np

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # Thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # Index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # Middle
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # Ring
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # Pinky
]


class OverlayRenderer:
    def __init__(
        self,
        window_title: str = "Thesidia-HandControl-Alpha",
        show_camera_background: bool = False,
        black_background: bool = True,
        draw_fps: bool = True,
        mirror: bool = True,
        constellation_enabled: bool = True,
        constellation_neighbors: int = 3,
        constellation_point_radius: int = 3,
        constellation_line_thickness: int = 1,
    ) -> None:
        self.window_title = window_title
        self.show_camera_background = show_camera_background
        self.black_background = black_background
        self.draw_fps = draw_fps
        self.mirror = mirror
        self.constellation_enabled = constellation_enabled
        self.constellation_neighbors = max(1, int(constellation_neighbors))
        self.constellation_point_radius = int(constellation_point_radius)
        self.constellation_line_thickness = int(constellation_line_thickness)

    def render(
        self,
        frame_bgr: np.ndarray,
        hands: List[Tuple[list, str]],
        gesture_name: Optional[str],
        symbol: Optional[str],
        fps: float,
    ) -> np.ndarray:
        h, w = frame_bgr.shape[:2]

        if self.show_camera_background and not self.black_background:
            canvas = frame_bgr.copy()
        else:
            canvas = np.zeros_like(frame_bgr)

        # Draw each hand landmarks and skeleton in white
        for landmarks, handedness in hands:
            self._draw_hand(canvas, landmarks, color=(255, 255, 255), thickness=2)
            if self.constellation_enabled:
                self._draw_constellation(canvas, landmarks, (255, 255, 255))

        # Title and labels in white
        y = 30
        cv2.putText(
            canvas,
            self.window_title,
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += 28
        if gesture_name:
            label = f"Gesture: {gesture_name}"
            cv2.putText(
                canvas,
                label,
                (16, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            y += 28
        if symbol:
            cv2.putText(
                canvas,
                f"Symbol: {symbol}",
                (16, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            y += 28
        if self.draw_fps:
            cv2.putText(
                canvas,
                f"FPS: {fps:.1f}",
                (16, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return canvas

    def _draw_hand(
        self,
        canvas: np.ndarray,
        landmarks: list,
        color=(255, 255, 255),
        thickness: int = 2,
    ) -> None:
        h, w = canvas.shape[:2]
        # Draw connections
        for a, b in HAND_CONNECTIONS:
            ax, ay = landmarks[a][0] * w, landmarks[a][1] * h
            bx, by = landmarks[b][0] * w, landmarks[b][1] * h
            cv2.line(
                canvas,
                (int(ax), int(ay)),
                (int(bx), int(by)),
                color,
                thickness,
                cv2.LINE_AA,
            )
        # Draw keypoints
        for x, y, _z in landmarks:
            cx, cy = int(x * w), int(y * h)
            cv2.circle(canvas, (cx, cy), 4, color, -1, lineType=cv2.LINE_AA)

    def _draw_constellation(
        self, canvas: np.ndarray, landmarks: list, color=(255, 255, 255)
    ) -> None:
        h, w = canvas.shape[:2]
        pts = np.array([[x * w, y * h] for (x, y, _z) in landmarks], dtype=np.float32)
        if len(pts) == 0:
            return
        # Draw star points
        for px, py in pts:
            cv2.circle(
                canvas,
                (int(px), int(py)),
                self.constellation_point_radius,
                color,
                -1,
                lineType=cv2.LINE_AA,
            )
        # Connect k-nearest neighbors
        k = min(self.constellation_neighbors, len(pts) - 1)
        if k <= 0:
            return
        # Compute pairwise distances
        diff = pts[:, None, :] - pts[None, :, :]
        dist = np.sqrt((diff**2).sum(axis=2))
        for i in range(len(pts)):
            order = np.argsort(dist[i])
            for j in order[1 : 1 + k]:  # skip self (index 0)
                p1 = tuple(np.round(pts[i]).astype(int))
                p2 = tuple(np.round(pts[j]).astype(int))
                cv2.line(
                    canvas,
                    p1,
                    p2,
                    color,
                    self.constellation_line_thickness,
                    cv2.LINE_AA,
                )
