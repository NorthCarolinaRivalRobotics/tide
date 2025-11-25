"""Utilities for recording and replaying Zenoh traffic using ROS bag files."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

try:
    from rosbags.highlevel import AnyReader, AnyReaderError
    from rosbags.rosbag2 import Writer
    from rosbags.rosbag2.writer import WriterError
    from rosbags.typesys import Stores, get_typestore, get_types_from_msg
    from rosbags.typesys.store import Typestore
except ImportError as exc:  # pragma: no cover
    raise ImportError("rosbags is required to record or play back Tide sessions") from exc

import zenoh

_RAW_MSG_TYPE = "tide_msgs/msg/Raw"
_RAW_MSG_DEF = "uint8[] data\n"

logger = logging.getLogger(__name__)

_active_recorder: Optional["RosbagRecorder"] = None


@dataclass
class _RecorderConfig:
    bag_path: Path
    typestore: Typestore


def _ensure_bytes(payload: object) -> bytes:
    """Convert a payload object into bytes."""

    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)

    if hasattr(payload, "__bytes__"):
        try:
            return bytes(payload)  # type: ignore[arg-type]
        except Exception:
            pass

    if isinstance(payload, str):
        return payload.encode("utf-8")

    try:
        return json.dumps(payload).encode("utf-8")
    except TypeError:
        return repr(payload).encode("utf-8")


class RosbagRecorder:
    """Record Zenoh traffic into a ROS bag."""

    def __init__(self, bag_path: Path | str) -> None:
        self.config = _RecorderConfig(
            bag_path=Path(bag_path),
            typestore=get_typestore(Stores.EMPTY),
        )
        self.config.typestore.register(get_types_from_msg(_RAW_MSG_DEF, _RAW_MSG_TYPE))
        self._message_cls = self.config.typestore.types[_RAW_MSG_TYPE]
        if self.config.bag_path.exists():
            if self.config.bag_path.is_dir():
                for child in self.config.bag_path.iterdir():
                    if child.is_file():
                        child.unlink()
                    else:
                        for nested in child.iterdir():
                            nested.unlink()
                        child.rmdir()
            else:
                self.config.bag_path.unlink()

        self._lock = threading.Lock()
        self._closed = False
        self._queue: "queue.Queue[Optional[Tuple[str, bytes, int]]]" = queue.Queue()
        self._writer = Writer(self.config.bag_path, version=9)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        connections: Dict[str, object] = {}
        try:
            self._writer.open()
            while True:
                item = self._queue.get()
                if item is None:
                    break
                topic, data, timestamp = item
                connection = connections.get(topic)
                if connection is None:
                    connection = self._writer.add_connection(
                        topic,
                        _RAW_MSG_TYPE,
                        typestore=self.config.typestore,
                    )
                    connections[topic] = connection

                ros_message = self._message_cls(data=np.frombuffer(data, dtype=np.uint8))
                raw_bytes = self.config.typestore.serialize_cdr(ros_message, _RAW_MSG_TYPE)
                self._writer.write(connection, timestamp, raw_bytes)
        finally:
            try:
                self._writer.close()
            except WriterError:
                pass

    def record(self, topic: str, payload: object, *, timestamp_ns: Optional[int] = None) -> None:
        """Persist a message in the bag."""

        if self._closed:
            return

        data = _ensure_bytes(payload)
        if not data:
            return

        timestamp = timestamp_ns if timestamp_ns is not None else time.time_ns()
        self._queue.put((topic, data, timestamp))

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._queue.put(None)
        self._thread.join()


class RosbagPlayer:
    """Replay messages from a ROS bag into the current Zenoh session."""

    def __init__(self, bag_path: Path | str, *, realtime: bool = True) -> None:
        self.bag_path = Path(bag_path)
        self.realtime = realtime
        self.typestore = get_typestore(Stores.EMPTY)
        self.typestore.register(get_types_from_msg(_RAW_MSG_DEF, _RAW_MSG_TYPE))
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._finished = threading.Event()
        self._error: Optional[Exception] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._finished.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _sleep_with_stop(self, duration: float) -> None:
        end = time.time() + duration
        while not self._stop_event.is_set():
            remaining = end - time.time()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.05))

    def _run(self) -> None:
        publishers: Dict[str, object] = {}
        session = None
        try:
            if not self.bag_path.exists():
                raise FileNotFoundError(self.bag_path)

            reader = AnyReader([self.bag_path], default_typestore=self.typestore)
            zenoh.init_log_from_env_or("error")
            session = zenoh.open(zenoh.Config())
            self._sleep_with_stop(0.1)

            start_timestamp: Optional[int] = None
            start_wall: Optional[float] = None

            with reader as bag_reader:
                for connection, timestamp, raw in bag_reader.messages():
                    if self._stop_event.is_set():
                        break

                    msg = self.typestore.deserialize_cdr(raw, _RAW_MSG_TYPE)
                    payload = bytes(msg.data)
                    topic = connection.topic

                    if self.realtime:
                        if start_timestamp is None:
                            start_timestamp = timestamp
                            start_wall = time.time()
                        else:
                            assert start_wall is not None
                            delay = (timestamp - start_timestamp) / 1_000_000_000
                            elapsed = time.time() - start_wall
                            sleep_time = delay - elapsed
                            if sleep_time > 0:
                                self._sleep_with_stop(sleep_time)

                    publisher = publishers.get(topic)
                    if publisher is None:
                        publisher = session.declare_publisher(topic)
                        publishers[topic] = publisher
                    publisher.put(payload)
        except (AnyReaderError, FileNotFoundError, WriterError, RuntimeError) as exc:
            self._error = exc
        finally:
            for publisher in publishers.values():
                try:
                    publisher.undeclare()
                except Exception:
                    pass
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
            self._finished.set()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._finished.wait(timeout)

    @property
    def error(self) -> Optional[Exception]:
        return self._error


def set_active_recorder(recorder: Optional[RosbagRecorder]) -> None:
    global _active_recorder
    _active_recorder = recorder


def clear_active_recorder() -> None:
    set_active_recorder(None)


def record_zenoh_message(topic: str, payload: object) -> None:
    if _active_recorder is None:
        return
    try:
        _active_recorder.record(topic, payload)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to record message for %s: %s", topic, exc)
