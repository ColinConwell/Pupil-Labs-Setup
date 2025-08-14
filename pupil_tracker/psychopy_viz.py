from typing import Optional, Sequence, Tuple
import time

from psychopy import core, event, visual

from .network import PupilCoreClient


def _map_pupil_norm_to_psychopy(norm_xy: Sequence[float]) -> Tuple[float, float]:
    """Convert Pupil Core norm_pos [0..1, 0..1] (origin top-left) to PsychoPy norm.

    PsychoPy 'norm' units: origin at screen center, x in [-1, 1], y in [-1, 1],
    y positive upwards. Pupil's y increases downwards, so flip.
    """
    x = float(norm_xy[0]) * 2.0 - 1.0
    y = (1.0 - float(norm_xy[1])) * 2.0 - 1.0
    return x, y


def run_psychopy_visualizer(
    host: str = "127.0.0.1",
    req_port: int = 50020,
    fullscreen: bool = False,
    monitor_name: str = "testMonitor",
    win_size: Optional[Tuple[int, int]] = (1280, 720),
    bg_color: str = "black",
    dot_color_ok: str = "lime",
    dot_color_low: str = "yellow",
    dot_color_bad: str = "red",
) -> None:
    """Open a PsychoPy window and draw live gaze as a dot with status text.

    - Requires Pupil Capture running with Pupil Remote enabled
    - Press 'q' to quit
    """
    client = PupilCoreClient(host=host, req_port=req_port)
    client.connect()
    sub = client.create_subscriber(topics=["gaze."])

    win = visual.Window(
        size=win_size,
        fullscr=fullscreen,
        monitor=monitor_name,
        color=bg_color,
        units="norm",
    )

    dot = visual.Circle(win, radius=0.02, edges=64, fillColor=dot_color_bad, lineColor=None)
    info = visual.TextStim(win, text="", pos=(-0.95, 0.9), height=0.04, alignText="left", color="white")

    last_gaze_xy = (0.0, 0.0)
    last_conf = 0.0
    last_ts = 0.0
    last_update_system = time.time()
    frames = 0
    fps = 0.0

    while True:
        msgs = sub.recv_all(max_messages=100)
        if msgs:
            for m in msgs:
                p = m.payload
                if not isinstance(p, dict):
                    continue
                if "norm_pos" in p:
                    last_gaze_xy = _map_pupil_norm_to_psychopy(p["norm_pos"])  # type: ignore[arg-type]
                    last_conf = float(p.get("confidence", 0.0))
                    last_ts = float(p.get("timestamp", 0.0))

        # Update FPS every 0.25s
        now = time.time()
        frames += 1
        if now - last_update_system >= 0.25:
            fps = frames / (now - last_update_system)
            frames = 0
            last_update_system = now

        # Pick color according to confidence
        if last_conf >= 0.8:
            color = dot_color_ok
        elif last_conf >= 0.5:
            color = dot_color_low
        else:
            color = dot_color_bad
        dot.fillColor = color
        dot.pos = last_gaze_xy

        info.text = (
            f"Gaze: ({last_gaze_xy[0]:+.3f}, {last_gaze_xy[1]:+.3f})\n"
            f"Conf: {last_conf:.2f}  |  Pupil ts: {last_ts:.3f}s\n"
            f"FPS: {fps:4.1f}  |  Press 'q' to quit"
        )

        dot.draw()
        info.draw()
        win.flip()

        keys = event.getKeys()
        if "q" in keys:
            break

        core.wait(0.001)

    sub.close()
    client.close()
    win.close()
