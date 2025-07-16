# Pose Estimator

Tide provides a simple pose estimator based on Lie groups. It combines twist
measurements with occasional pose observations using an EKF running directly on
the manifold.

## Expected Topics

The estimator subscribes to:

- **Twist measurements** – `Twist2D` or `Twist3D` messages representing body
  velocity.
- **Pose measurements** – `Pose2D` or `Pose3D` messages that have already been
  transformed into the robot frame.

It publishes the filtered pose on `pose_estimate` by default.

## Algorithm Overview

1. **Propagation** – incoming twists are integrated using the exponential map of
   `SE(2)` or `SE(3)`.  The covariance is propagated using the adjoint matrix.
2. **Update** – when a pose measurement arrives, the error between the current
   estimate and the measurement is computed using the group logarithm.  A
   standard Kalman update is performed in the tangent space.

Both `SE2Estimator` and `SE3Estimator` are provided and used by
`PoseEstimatorNode`.

## Example

The script [`tide/examples/pose_estimator_demo.py`](../tide/examples/pose_estimator_demo.py)
shows a minimal simulation.  It generates noisy twist and pose data from a
simulated trajectory and demonstrates that the filter converges:

```bash
uv run python tide/examples/pose_estimator_demo.py
```
