import argparse

from pupil_tracker.opencv_stream import run_opencv_visualizer
from pupil_tracker.psychopy_viz import run_psychopy_visualizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch live Pupil Core gaze visualizer")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host/IP where Pupil Capture runs")
    parser.add_argument("--port", type=int, default=50020, help="Pupil Remote REQ port (default 50020)")
    parser.add_argument("--fullscreen", action="store_true", help="Open PsychoPy visualizer fullscreen")
    parser.add_argument("--use-psychopy", action="store_true", help="Use PsychoPy renderer instead of OpenCV window")
    args = parser.parse_args()

    if args.use_psychopy:
        run_psychopy_visualizer(host=args.host, req_port=args.port, fullscreen=args.fullscreen)
    else:
        run_opencv_visualizer(host=args.host, req_port=args.port)


if __name__ == "__main__":
    main()
