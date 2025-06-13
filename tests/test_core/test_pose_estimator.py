import numpy as np
from tide.components.pose_estimator import SE2Estimator
from tide.core.geometry import SE2


def test_se2_estimator_converges():
    est = SE2Estimator()
    true_pose = SE2.identity()
    dt = 0.1
    twist = np.array([0.3, 0.0, 0.1])

    for _ in range(50):
        true_pose = true_pose * SE2.exp(twist * dt)
        est.propagate(twist, dt)
        est.update(true_pose)

    err = np.linalg.norm((est.pose.inverse() * true_pose).log())
    assert err < 1e-6
