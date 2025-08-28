import time

from tide.core.node import BaseNode
from tide.core.utils import launch_from_config
from tide.config import TideConfig, NodeConfig
from tide.models.serialization import to_zenoh_value


class ConstantPublisher(BaseNode):
    """Node that continuously publishes a constant value to a topic."""

    GROUP = "pub"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.config or {}
        self.topic = cfg.get("topic", "state")
        self.value = float(cfg.get("value", 0.0))

    def step(self):
        self.put(self.topic, to_zenoh_value(self.value))


class CommandRecorder(BaseNode):
    """Node that records command messages from a topic."""

    GROUP = "sub"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.config or {}
        self.topic = cfg.get("topic", "cmd")
        self.received = []
        self.subscribe(self.topic, self._on_cmd)

    def _on_cmd(self, data):
        try:
            self.received.append(float(data))
        except Exception:
            self.received.append(data)

    def step(self):
        pass


def test_pid_node_basic():
    cfg = TideConfig(
        nodes=[
            NodeConfig(
                type="tests.test_core.test_pid_node.ConstantPublisher",
                params={"robot_id": "robot", "topic": "/robot/ref", "value": 10.0},
            ),
            NodeConfig(
                type="tests.test_core.test_pid_node.ConstantPublisher",
                params={"robot_id": "robot", "topic": "/robot/state", "value": 3.0},
            ),
            NodeConfig(
                type="tide.components.PIDNode",
                params={
                    "robot_id": "robot",
                    "k_p": 1.0,
                    "k_i": 0.0,
                    "k_d": 0.0,
                    "state_topic": "/robot/state",
                    "reference_topic": "/robot/ref",
                    "command_topic": "/robot/cmd",
                    "hz": 20.0,
                },
            ),
            NodeConfig(
                type="tests.test_core.test_pid_node.CommandRecorder",
                params={"robot_id": "robot", "topic": "/robot/cmd"},
            ),
        ]
    )

    nodes, procs = launch_from_config(cfg)

    # Allow time for messages to be exchanged
    time.sleep(0.5)

    for n in nodes:
        n.stop()
    for n in nodes:
        for t in n.threads:
            t.join(timeout=1.0)
    for p in procs:
        p.terminate()

    recorder = nodes[-1]
    assert getattr(recorder, "received", None), "no command published"
    assert any(abs(val - 7.0) < 1e-3 for val in recorder.received)
