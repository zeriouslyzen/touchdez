from typing import List, Optional, Tuple

from pythonosc.udp_client import SimpleUDPClient


class OSCEmitter:
    def __init__(
        self, host: str = "127.0.0.1", port: int = 9000, send_landmarks: bool = False
    ) -> None:
        self.client = SimpleUDPClient(host, int(port))
        self.send_landmarks = bool(send_landmarks)

    def send_gesture(self, gesture_name: Optional[str], symbol: Optional[str]) -> None:
        name = gesture_name or "NONE"
        sym = symbol or ""
        self.client.send_message("/thesidia/gesture", [name, sym])

    def send_fps(self, fps: float) -> None:
        self.client.send_message("/thesidia/fps", float(fps))

    def send_landmarks(self, hands: List[Tuple[list, str]]) -> None:
        if not self.send_landmarks:
            return
        # Send first hand only to keep bandwidth minimal
        if not hands:
            self.client.send_message("/thesidia/hand/0/landmarks", [])
            return
        landmarks, handedness = hands[0]
        flat = []
        for x, y, z in landmarks:
            flat.extend([float(x), float(y), float(z)])
        self.client.send_message("/thesidia/hand/0/landmarks", flat)
        self.client.send_message("/thesidia/hand/0/handedness", handedness)
