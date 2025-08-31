import time

from tide.core.node import BaseNode
from tide.core.utils import launch_from_config
from tide.config import TideConfig, NodeConfig
from tide.models.common import Twist2D, Vector2


class ConstantTwistPublisher(BaseNode):
    """Continuously publish a fixed Twist2D."""

    GROUP = "pub"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.config or {}
        self.topic = cfg.get("topic", "/robot/cmd")
        self.value = float(cfg.get("value", 0.0))

    def step(self) -> None:
        msg = Twist2D(linear=Vector2(x=self.value, y=0.0))
        self.put(self.topic, msg)


class TwistRecorder(BaseNode):
    """Record incoming Twist2D messages."""

    GROUP = "sub"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.config or {}
        self.topic = cfg.get("topic", "/robot/cmd/mux")
        self.received = []
        self.subscribe(self.topic, self._on_msg)

    def _on_msg(self, data):
        try:
            self.received.append(Twist2D.model_validate(data))
        except Exception:
            self.received.append(data)

    def step(self) -> None:
        pass


def test_mux_node_priority_selection():
    cfg = TideConfig(
        nodes=[
            NodeConfig(
                type="tests.test_components.test_mux_node.ConstantTwistPublisher",
                params={"robot_id": "robot", "topic": "/robot/cmd/teleop", "value": 2.0},
            ),
            NodeConfig(
                type="tests.test_components.test_mux_node.ConstantTwistPublisher",
                params={"robot_id": "robot", "topic": "/robot/cmd/autonomy", "value": 1.0},
            ),
            NodeConfig(
                type="tide.components.MuxNode",
                params={
                    "robot_id": "robot",
                    "inputs": [
                        {"topic": "/robot/cmd/teleop", "priority": 0},
                        {"topic": "/robot/cmd/autonomy", "priority": 1},
                    ],
                    "output_topic": "/robot/cmd/mux",
                    "msg_type": "tide.models.common.Twist2D",
                    "hz": 20.0,
                },
            ),
            NodeConfig(
                type="tests.test_components.test_mux_node.TwistRecorder",
                params={"robot_id": "robot", "topic": "/robot/cmd/mux"},
            ),
        ]
    )

    nodes, procs = launch_from_config(cfg)

    # Allow messages to propagate
    time.sleep(0.5)

    for n in nodes:
        n.stop()
    for n in nodes:
        for t in n.threads:
            t.join(timeout=1.0)
    for p in procs:
        p.terminate()

    recorder = nodes[-1]
    assert getattr(recorder, "received", None), "no message received"
    twists = [m for m in recorder.received if isinstance(m, Twist2D)]
    assert twists and max(t.linear.x for t in twists) == 2.0