"""Support nodes for rosbag recording tests."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict

from tide.core.node import BaseNode


class PublisherNode(BaseNode):
    """Publish sequential counters for testing."""

    GROUP = "test"
    hz = 20.0

    def __init__(self, *, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        self.counter = 0
        cfg = config or {}
        self.topic = cfg.get("topic", "counter")
        self.robot_id = cfg.get("robot_id", self.ROBOT_ID)
        self.max_count = int(cfg.get("max_count", 10))
        self._started = False

    def step(self) -> None:
        if not self._started:
            time.sleep(0.05)
            self._started = True
        payload = {"robot": self.robot_id, "count": self.counter}
        self.put(self.topic, payload)
        self.counter = (self.counter + 1) % (self.max_count + 1)


class FileCollectorNode(BaseNode):
    """Collect messages and append them to a log file."""

    GROUP = "test"
    hz = 10.0

    def __init__(self, *, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}
        self.topic = cfg.get("topic", "counter")
        log_path = cfg.get("log_path")
        if not log_path:
            raise ValueError("log_path must be provided for FileCollectorNode")
        self.log_path = Path(log_path)
        self.log_path.write_text(json.dumps([]))
        self._lock = threading.Lock()
        self._records: list[Dict[str, Any]] = []
        self.subscribe(self.topic, self._on_message)

    def _on_message(self, message: Dict[str, Any]) -> None:
        with self._lock:
            self._records.append(message)
            self.log_path.write_text(json.dumps(self._records))

    def step(self) -> None:
        # Collector node is event driven via the subscription callback.
        pass
