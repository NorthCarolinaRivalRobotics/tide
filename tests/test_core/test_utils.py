import math

from tide.models.common import Quaternion


def test_quaternion_roundtrip():
    angles = (
        0.1,  # roll
        -0.2,  # pitch
        0.3,  # yaw
    )
    q = Quaternion.from_euler(*angles)
    recovered = q.to_euler()

    assert math.isclose(recovered[0], angles[0], abs_tol=1e-6)
    assert math.isclose(recovered[1], angles[1], abs_tol=1e-6)
    assert math.isclose(recovered[2], angles[2], abs_tol=1e-6)
