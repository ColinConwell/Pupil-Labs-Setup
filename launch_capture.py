import argparse

from pupil_tracker.psychopy_viz import run_psychopy_visualizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch live Pupil Core gaze visualizer (PsychoPy)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host/IP where Pupil Capture runs")
    parser.add_argument("--port", type=int, default=50020, help="Pupil Remote REQ port (default 50020)")
    parser.add_argument("--fullscreen", action="store_true", help="Open visualizer fullscreen")
    args = parser.parse_args()

    run_psychopy_visualizer(host=args.host, req_port=args.port, fullscreen=args.fullscreen)


if __name__ == "__main__":
    main()
