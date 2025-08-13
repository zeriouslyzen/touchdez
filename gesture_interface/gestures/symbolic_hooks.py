import math
from typing import List, Optional, Tuple


def _distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class GestureClassifier:
    """Heuristic gesture classifier. Replace with ML later.

    Gestures:
      - OPEN_PALM: all fingertips far from wrist
      - FIST: all fingertips near wrist
      - POINT: index extended, others curled
    """

    def __init__(self) -> None:
        pass

    def classify(
        self, hands: List[Tuple[list, str]]
    ) -> Tuple[Optional[str], Optional[str]]:
        if not hands:
            return None, None
        landmarks, handedness = hands[0]
        wrist = landmarks[0]
        tips = [
            landmarks[i] for i in [4, 8, 12, 16, 20]
        ]  # thumb,index,middle,ring,pinky tips
        tip_dists = [_distance(t, wrist) for t in tips]

        # Normalize distances by hand scale (wrist to middle MCP index 9)
        scale_ref = _distance(wrist, landmarks[9]) + 1e-6
        norm_dists = [d / scale_ref for d in tip_dists]

        open_thresh = 1.8
        fist_thresh = 1.0

        if all(d > open_thresh for d in norm_dists[1:]):  # ignore thumb for strictness
            return "OPEN_PALM", "#FLAME[RISE]"

        if all(d < fist_thresh for d in norm_dists):
            return "FIST", "#STONE[SEAL]"

        # POINT: index large, others small
        if norm_dists[1] > open_thresh and all(
            d < fist_thresh for i, d in enumerate(norm_dists) if i != 1
        ):
            return "POINT", "#ARROW[TRUE]"

        return None, None
