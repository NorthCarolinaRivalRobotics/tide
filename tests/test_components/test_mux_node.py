import pytest

from tide.components.mux_node import MuxNode
from tide.models.common import Twist2D, Vector2


def _twist(x: float) -> dict:
    return Twist2D(linear=Vector2(x=x, y=0.0)).model_dump(mode="json")


def test_mux_node_priority_selection():
    node = MuxNode(
        config={
            "robot_id": "robot",
            "inputs": [
                {"topic": "cmd/teleop", "priority": 0},
                {"topic": "cmd/autonomy", "priority": 1},
            ],
            "output_topic": "cmd/mux",
            "msg_type": Twist2D,
        }
    )
    # Avoid network usage
    node.session = None
    published: list[Twist2D] = []
    node.put = lambda topic, msg: published.append(msg)

    high_key = node._make_key("cmd/teleop")
    low_key = node._make_key("cmd/autonomy")

    # Only low-priority message
    node._latest_values[low_key] = _twist(1.0)
    node.step()
    assert published and isinstance(published[-1], Twist2D)
    assert published[-1].linear.x == 1.0
    published.clear()

    # High- and low-priority messages arrive simultaneously
    node._latest_values[high_key] = _twist(2.0)
    node._latest_values[low_key] = _twist(3.0)
    node.step()
    assert published and published[-1].linear.x == 2.0
    published.clear()

    # High-priority idle, low-priority publishes again
    node._latest_values[low_key] = _twist(4.0)
    node.step()
    assert published and published[-1].linear.x == 4.0
