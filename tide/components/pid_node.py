import time
from typing import Any

from tide.core.node import BaseNode
from tide.models.serialization import to_zenoh_value


class PIDNode(BaseNode):
    """Simple PID controller node."""

    GROUP = "controller"

    def __init__(self, *, config: dict | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}

        self.k_p = float(cfg.get("k_p", 1.0))
        self.k_i = float(cfg.get("k_i", 0.0))
        self.k_d = float(cfg.get("k_d", 0.0))
        self.state_topic = cfg.get("state_topic", "state")
        self.reference_topic = cfg.get("reference_topic", "reference")
        self.command_topic = cfg.get("command_topic", "command")
        self.hz = float(cfg.get("hz", self.hz))

        self._integral = 0.0
        self._prev_error = 0.0
        self._last_time = time.time()
        self.state: float = 0.0
        self.reference: float = 0.0

        self.subscribe(self.state_topic)
        self.subscribe(self.reference_topic)

    def step(self) -> None:
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        val = self.take(self.state_topic)
        if isinstance(val, (int, float)):
            self.state = float(val)

        ref = self.take(self.reference_topic)
        if isinstance(ref, (int, float)):
            self.reference = float(ref)

        error = self.reference - self.state
        self._integral += error * dt
        derivative = (error - self._prev_error) / dt if dt > 0 else 0.0
        output = self.k_p * error + self.k_i * self._integral + self.k_d * derivative
        self._prev_error = error

        self.put(self.command_topic, to_zenoh_value(output))
