import threading
from typing import Any, Dict, List, Optional, Tuple


class DashboardState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "gesture": None,
            "symbol": None,
            "fps": 0.0,
            "landmarks": [],  # [[x,y], ...] normalized 0..1
        }

    def update(
        self,
        gesture: Optional[str],
        symbol: Optional[str],
        fps: float,
        landmarks: Optional[List[Tuple[float, float]]] = None,
    ) -> None:
        with self._lock:
            self._state["gesture"] = gesture
            self._state["symbol"] = symbol
            self._state["fps"] = float(fps)
            if landmarks is not None:
                self._state["landmarks"] = [
                    [float(x), float(y)] for (x, y) in landmarks
                ]

    def get(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)


GLOBAL_DASHBOARD_STATE = DashboardState()
