import time

from tide.bt import Action, Sequence, Status
from tide.config import NodeConfig, TideConfig
from tide.core.utils import launch_from_config


def build_tree():
    def mark(bb):
        bb["ticks"] = bb.get("ticks", 0) + 1
        return Status.SUCCESS

    return Sequence([Action(mark)])


def test_behavior_tree_node_ticks_tree():
    cfg = TideConfig(
        nodes=[
            NodeConfig(
                type="tide.components.BehaviorTreeNode",
                params={
                    "robot_id": "robot",
                    "tree": "tests.test_components.test_behavior_tree_node.build_tree",
                    "blackboard": {},
                    "hz": 20.0,
                },
            )
        ]
    )

    nodes, procs = launch_from_config(cfg)
    time.sleep(0.3)

    for n in nodes:
        n.stop()
        for t in n.threads:
            t.join(timeout=1.0)
    for p in procs:
        p.terminate()

    bb = nodes[0].blackboard
    assert bb.get("ticks", 0) > 0
