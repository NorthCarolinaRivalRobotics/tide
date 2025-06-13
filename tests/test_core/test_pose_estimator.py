import numpy as np
import pytest
from tide.components.pose_estimator import SE2Estimator, SE3Estimator
from tide.core.geometry import SE2, SE3


@pytest.mark.parametrize(
    "twist",
    [
        np.array([0.3, 0.0, 0.1]),
        np.array([0.0, 0.0, 0.0]),
        np.array([0.1, 0.0, 0.0]),
        np.array([0.0, 0.0, 0.2]),
    ],
)
def test_se2_estimator_converges(twist):
    est = SE2Estimator()
    true_pose = SE2.identity()
    dt = 0.1

    for _ in range(50):
        true_pose = true_pose * SE2.exp(twist * dt)
        est.propagate(twist, dt)
        est.update(true_pose)

    err = np.linalg.norm((est.pose.inverse() * true_pose).log())
    assert err < 1e-6


def test_se3_estimator_converges():
    est = SE3Estimator()
    true_pose = SE3.identity()
    dt = 0.1
    twist = np.array([0.1, -0.2, 0.3, 0.05, -0.04, 0.02])

    for _ in range(50):
        true_pose = true_pose * SE3.exp(twist * dt)
        est.propagate(twist, dt)
        est.update(true_pose)

    err = np.linalg.norm((est.pose.inverse() * true_pose).log())
    assert err < 1e-6
