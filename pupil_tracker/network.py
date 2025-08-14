import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import msgpack
import zmq


@dataclass
class PupilMessage:
    """Container for a single message from Pupil Core PUB socket."""

    topic: str
    payload: Dict
    recv_time_monotonic: float


class PupilCoreClient:
    """Minimal client for Pupil Core Network API (Pupil Remote plugin).

    - Connects to request (REQ) port (default 50020)
    - Discovers SUB and PUB ports via commands
    - Subscribes to topics and yields msgpack-decoded dicts

    Reference: https://docs.pupil-labs.com/core/developer/
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        req_port: int = 50020,
        recv_hwm: int = 1000,
        recv_timeout_ms: int = 50,
    ) -> None:
        self.host = host
        self.req_port = req_port
        self.recv_hwm = recv_hwm
        self.recv_timeout_ms = recv_timeout_ms

        self._ctx: Optional[zmq.Context] = None
        self._req: Optional[zmq.Socket] = None

    def connect(self) -> None:
        if self._ctx is not None:
            return
        self._ctx = zmq.Context.instance()
        self._req = self._ctx.socket(zmq.REQ)
        self._req.setsockopt(zmq.LINGER, 0)
        self._req.connect(f"tcp://{self.host}:{self.req_port}")

    def close(self) -> None:
        if self._req is not None:
            self._req.close(0)
            self._req = None
        if self._ctx is not None:
            self._ctx.term()
            self._ctx = None

    # ---- Request helpers ----
    def _send_cmd(self, cmd: str) -> str:
        """Send a simple string command and return string response."""
        if self._req is None:
            raise RuntimeError("Client not connected. Call connect().")
        self._req.send_string(cmd)
        return self._req.recv_string()

    def get_sub_port(self) -> int:
        resp = self._send_cmd("SUB_PORT")
        return int(resp)

    def get_pub_port(self) -> int:
        resp = self._send_cmd("PUB_PORT")
        return int(resp)

    def send_notification(self, notification: Dict) -> None:
        """Send a notification via the REP socket using msgpack notify payload."""
        if self._req is None:
            raise RuntimeError("Client not connected. Call connect().")
        payload = ("notify.%s" % notification.get("subject", ""), notification)
        packed = msgpack.packb(payload, use_bin_type=True)
        self._req.send(packed)
        _ = self._req.recv()

    def create_subscriber(
        self,
        topics: Optional[Sequence[str]] = None,
        fast: bool = True,
    ) -> "PupilCoreSubscriber":
        if self._ctx is None:
            raise RuntimeError("Client not connected. Call connect().")
        sub_port = self.get_sub_port()
        return PupilCoreSubscriber(
            ctx=self._ctx,
            host=self.host,
            sub_port=sub_port,
            recv_hwm=self.recv_hwm,
            recv_timeout_ms=self.recv_timeout_ms,
            topics=topics,
            fast=fast,
        )


class PupilCoreSubscriber:
    """Subscriber that receives topic + msgpack frames from Pupil Core."""

    def __init__(
        self,
        ctx: zmq.Context,
        host: str,
        sub_port: int,
        recv_hwm: int,
        recv_timeout_ms: int,
        topics: Optional[Sequence[str]] = None,
        fast: bool = True,
    ) -> None:
        self._socket = ctx.socket(zmq.SUB)
        self._socket.setsockopt(zmq.RCVHWM, recv_hwm)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._socket.rcvtimeo = recv_timeout_ms
        self._socket.connect(f"tcp://{host}:{sub_port}")

        if not topics:
            self._socket.setsockopt(zmq.SUBSCRIBE, b"")
        else:
            for t in topics:
                self._socket.setsockopt(zmq.SUBSCRIBE, t.encode("utf-8"))

        self._fast_unpack = fast

    def close(self) -> None:
        self._socket.close(0)

    def recv(self) -> Optional[PupilMessage]:
        """Receive a single message if available; returns None on timeout."""
        try:
            frames = self._socket.recv_multipart(flags=0)
        except zmq.Again:
            return None
        if not frames:
            return None
        if len(frames) == 1:
            topic = ""
            packed = frames[0]
        else:
            topic = frames[0].decode("utf-8", errors="replace")
            packed = frames[1]

        payload = msgpack.unpackb(packed, raw=False, use_list=True)
        return PupilMessage(topic=topic, payload=payload, recv_time_monotonic=time.monotonic())

    def recv_all(self, max_messages: int = 100) -> List[PupilMessage]:
        """Drain up to N messages without blocking longer than socket timeout."""
        messages: List[PupilMessage] = []
        for _ in range(max_messages):
            msg = self.recv()
            if msg is None:
                break
            messages.append(msg)
        return messages
