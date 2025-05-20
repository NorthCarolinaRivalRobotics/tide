#!/usr/bin/env python3
"""Example node that publishes a constant cmd/twist command."""

import time
from tide.core.node import BaseNode
from tide.models import Twist2D, Vector2
from tide.models.serialization import to_zenoh_value
from tide import CmdTopic


class CmdTwistPublisher(BaseNode):
    """Sends a simple forward velocity command."""

    ROBOT_ID = "mockbot"
    GROUP = "teleop"

    hz = 2.0  # publish at 2 Hz

    def step(self) -> None:
        cmd = Twist2D(linear=Vector2(x=0.2), angular=0.0)
        self.put(CmdTopic.TWIST.value, to_zenoh_value(cmd))
        print(f"Sent command: {cmd}")


def main() -> None:
    node = CmdTwistPublisher()
    node.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()
        print("Stopped")


if __name__ == "__main__":
    main()
