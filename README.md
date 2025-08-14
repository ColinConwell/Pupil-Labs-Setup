# Pupil-Tracker Mini Library

Convenience wrappers for the Pupil Labs Core Network API plus a PsychoPy visualizer.

- `pupil_tracker/network.py`: Minimal ZeroMQ client and subscriber for Pupil Core
- `pupil_tracker/psychopy_viz.py`: PsychoPy visualizer that renders live gaze
- `launch_capture.py`: CLI to open the visualizer window

References: [Pupil Core Developer Docs](https://docs.pupil-labs.com/core/developer/), [VirtualHome Getting Started](http://virtual-home.org/documentation/master/get_started/get_started.html#id4)

## Prerequisites

- Hardware: Pupil Labs Pupil Core eye tracker (binocular or monocular)
- Software: Pupil Capture app installed for your OS, with the "Pupil Remote" (Network API) plugin available/enabled
- Python 3.9+ recommended

### Install Pupil Capture and enable the Network API

1. Install and start Pupil Capture.
2. Connect the Pupil Core headset (USB) and ensure world/eye cameras stream in Capture.
3. In Pupil Capture, enable the "Pupil Remote" plugin (Network API). This exposes a REQ/REP control endpoint (default port 50020) and a PUB/SUB data endpoint (SUB port is discovered via request). See the developer docs for the realtime API details: [Pupil Core Developer Docs](https://docs.pupil-labs.com/core/developer/).
4. Perform a calibration in Pupil Capture so that `gaze.*` topics are produced with valid `norm_pos` and `confidence`.

Notes:
- Default REQ port is 50020; the SUB port is provided by the `SUB_PORT` request.
- Allow Capture through macOS firewall prompts so ZMQ sockets are reachable.

## Install this Mini Library

```bash
# Optional: create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

If you encounter difficulties installing PsychoPy via pip on macOS, consider installing via conda-forge (recommended by PsychoPy) or ensure XQuartz and audio backends are available. For most systems, the provided requirements are sufficient.

## Launch the live gaze visualizer (MVP)

- Ensure Pupil Capture is running, Pupil Remote is enabled, and calibration is done.
- Run the visualizer:

```bash
python launch_capture.py --host 127.0.0.1 --port 50020
```

- A window will appear. A dot will reflect live gaze; its color encodes confidence (red=low, yellow=medium, lime=high). Press `q` to quit.

## Use inside a PsychoPy experiment

You can embed the client in your PsychoPy task to access gaze in real time.

High-level steps:

1. Start Pupil Capture with Pupil Remote enabled and calibrate.
2. In your PsychoPy script, import and connect the client:
   - Create a `PupilCoreClient`, call `connect()`, then `create_subscriber(topics=["gaze."])`.
   - Inside your trial loop, call `sub.recv_all()` each frame to get the latest gaze messages and use the latest `norm_pos`/`confidence`.
3. Clean up with `sub.close()` and `client.close()` when done.

## Troubleshooting

- No gaze/dot not moving:
  - Verify the Pupil Remote plugin is enabled in Capture.
  - Verify calibration has been completed (gaze topics contain `norm_pos`).
  - Check that `--host` and `--port` match your Capture machine/port (default REQ 50020).
  - Firewalls: Allow incoming connections for Pupil Capture.
- Stuttering updates:
  - Reduce system load; ensure sufficient lighting and stable detection.
  - Our subscriber uses a small timeout and drains up to 100 messages per frame to keep latency low.
- PsychoPy installation issues on macOS:
  - Consider installing via `conda` (PsychoPy recommends this route) or ensure platform dependencies are available.

## Project layout

- `pupil_tracker/network.py`: ZMQ REQ helper + SUB client to decode msgpack messages (topics like `gaze.3d.*`, `pupil.*`, `surfaces.*`).
- `pupil_tracker/psychopy_viz.py`: Visualizes `gaze.*` messages; maps Pupil `norm_pos` ([0,1] origin top-left) to PsychoPy `norm` (origin center, y-up).
- `launch_capture.py`: CLI entry point to start the visualizer.

## Related docs and tools

- Pupil Core realtime/network API overview and data formats (pupil, gaze, surfaces): [Pupil Core Developer Docs](https://docs.pupil-labs.com/core/developer/)
- If you are also using the VirtualHome Unity simulator in your research pipeline, follow its install and usage guide: [VirtualHome Getting Started](http://virtual-home.org/documentation/master/get_started/get_started.html#id4)
