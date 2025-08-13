from typing import List, Optional, Tuple

import mediapipe as mp


class HandLandmarkDetector:
    """Thin wrapper around MediaPipe Hands."""

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=1,
        )

    def process(self, frame_rgb) -> List[Tuple[list, str]]:
        """
        Returns a list of (landmarks, handedness) pairs for each detected hand.
        - landmarks: list of 21 (x, y, z) normalized coords
        - handedness: "Left" or "Right"
        """
        results = self._hands.process(frame_rgb)
        output: List[Tuple[list, str]] = []
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                lm = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                label = handedness.classification[0].label
                output.append((lm, label))
        return output

    def __del__(self):
        try:
            self._hands.close()
        except Exception:
            pass
