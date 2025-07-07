import numpy as np
from tide.components.pose_estimator import SE2Estimator
from tide.core.geometry import SE2


def simulate():
    est = SE2Estimator()
    true_pose = SE2.identity()
    dt = 0.1
    twist = np.array([0.5, 0.0, 0.2])

    errors = []
    for i in range(200):
        true_pose = true_pose * SE2.exp(twist * dt)
        meas_twist = twist + np.random.normal(scale=0.05, size=3)
        est.propagate(meas_twist, dt)
        if i % 5 == 0:
            meas_pose = true_pose * SE2.exp(np.random.normal(scale=0.02, size=3))
            est.update(meas_pose)
        err = (est.pose.inverse() * true_pose).log()
        errors.append(np.linalg.norm(err))
    print(f"final error: {errors[-1]:.4f}")


if __name__ == "__main__":
    simulate()
