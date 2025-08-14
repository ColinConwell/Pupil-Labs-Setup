from typing import Optional, Sequence
import time

import cv2
import numpy as np

from .network import PupilCoreClient


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def run_opencv_visualizer(
    host: str = "127.0.0.1",
    req_port: int = 50020,
    window_name: str = "Pupil Gaze",
    width: int = 960,
    height: int = 540,
    max_fps: int = 60,
) -> None:
    """Open an OpenCV window and draw live gaze dot and status text.

    - Requires Pupil Capture running with Pupil Remote enabled
    - Press 'q' or ESC to quit
    """
    client = PupilCoreClient(host=host, req_port=req_port)
    client.connect()
    sub = client.create_subscriber(topics=["gaze."])

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)

    last_norm = (0.5, 0.5)  # Pupil norm_pos in [0..1] with origin top-left
    last_conf = 0.0
    last_ts = 0.0
    frames = 0
    fps = 0.0
    last_update = time.time()

    delay_ms = max(1, int(1000 / max_fps))

    try:
        while True:
            msgs = sub.recv_all(max_messages=200)
            if msgs:
                for m in msgs:
                    p = m.payload
                    if not isinstance(p, dict):
                        continue
                    if "norm_pos" in p:
                        try:
                            nx = float(p["norm_pos"][0])
                            ny = float(p["norm_pos"][1])
                            last_norm = (
                                _clamp(nx, 0.0, 1.0),
                                _clamp(ny, 0.0, 1.0),
                            )
                        except Exception:
                            pass
                        last_conf = float(p.get("confidence", 0.0))
                        last_ts = float(p.get("timestamp", 0.0))

            # Create background
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # Crosshair
            cv2.line(frame, (width // 2, 0), (width // 2, height), (40, 40, 40), 1)
            cv2.line(frame, (0, height // 2), (width, height // 2), (40, 40, 40), 1)

            # Map norm -> pixel (OpenCV uses top-left origin, y down)
            px = int(last_norm[0] * (width - 1))
            py = int(last_norm[1] * (height - 1))

            # Color based on confidence
            if last_conf >= 0.8:
                color = (0, 255, 0)  # lime
            elif last_conf >= 0.5:
                color = (0, 255, 255)  # yellow
            else:
                color = (0, 0, 255)  # red

            cv2.circle(frame, (px, py), radius=12, color=color, thickness=-1)

            # Update FPS (every 0.25s)
            now = time.time()
            frames += 1
            if now - last_update >= 0.25:
                fps = frames / (now - last_update)
                frames = 0
                last_update = now

            # Status text
            text_lines = [
                f"Gaze: ({last_norm[0]:.3f}, {last_norm[1]:.3f}) px=({px},{py})",
                f"Conf: {last_conf:.2f}  |  Pupil ts: {last_ts:.3f}s  |  FPS: {fps:4.1f}",
                "Press 'q' or ESC to quit",
            ]
            y0 = 24
            for i, t in enumerate(text_lines):
                y = y0 + i * 22
                cv2.putText(frame, t, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(delay_ms) & 0xFF
            if key in (27, ord('q')):  # ESC or 'q'
                break
    finally:
        sub.close()
        client.close()
        cv2.destroyWindow(window_name)
