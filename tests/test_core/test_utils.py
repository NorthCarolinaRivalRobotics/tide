import math
import os
import sys

from tide.core.utils import (
    quaternion_from_euler,
    euler_from_quaternion,
    add_project_root_to_path,
)


def test_quaternion_roundtrip():
    angles = (
        0.1,  # roll
        -0.2,  # pitch
        0.3,  # yaw
    )
    q = quaternion_from_euler(*angles)
    recovered = euler_from_quaternion(q)

    assert math.isclose(recovered[0], angles[0], abs_tol=1e-6)
    assert math.isclose(recovered[1], angles[1], abs_tol=1e-6)
    assert math.isclose(recovered[2], angles[2], abs_tol=1e-6)


def test_add_project_root_to_path(tmp_path):
    project_root = tmp_path / "project"
    nodes_dir = project_root / "nodes"
    nodes_dir.mkdir(parents=True)
    script = nodes_dir / "dummy.py"
    script.write_text("", encoding="utf-8")

    added = add_project_root_to_path(str(script))
    assert added == str(project_root)
    assert added in sys.path

    # cleanup
    sys.path.remove(added)
    assert added not in sys.path
