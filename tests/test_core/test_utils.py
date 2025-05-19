import math

from tide.core.utils import quaternion_from_euler, euler_from_quaternion


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
