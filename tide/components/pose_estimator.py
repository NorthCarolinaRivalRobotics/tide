"""Pose estimation using Lie group EKF."""

from __future__ import annotations

import time
import logging
from typing import Optional

import numpy as np

from tide.core.node import BaseNode
from tide.core.geometry import (
    SE2,
    SE3,
    adjoint_se2,
    adjoint_se3,
    SO2,
    SO3,
    Quaternion as GeoQuat,
)
from tide.models import Twist2D, Twist3D, Pose2D, Pose3D
from tide.models.serialization import to_zenoh_value


class _EKFBase:
    """Shared EKF logic for Lie groups."""

    def __init__(self, dim: int, group_cls, adj_fn) -> None:
        self._group_cls = group_cls
        self._adj_fn = adj_fn
        self.pose = group_cls.identity()
        self.P = np.eye(dim) * 1e-3
        self.Q = np.eye(dim) * 1e-4
        self.R = np.eye(dim) * 1e-2

    def propagate(self, twist: np.ndarray, dt: float) -> None:
        delta = twist * dt
        inc = self._group_cls.exp(delta)
        self.pose = self.pose * inc
        Ad = self._adj_fn(inc)
        self.P = Ad @ self.P @ Ad.T + self.Q * dt * dt

    def update(self, measurement) -> None:
        err = (self.pose.inverse() * measurement).log()
        S = self.P + self.R
        K = np.linalg.solve(S.T, self.P.T).T
        delta = K @ err
        self.pose = self.pose * self._group_cls.exp(delta)
        self.P = (np.eye(self.P.shape[0]) - K) @ self.P


class SE2Estimator(_EKFBase):
    """Extended Kalman Filter on SE(2)."""

    def __init__(self) -> None:
        super().__init__(3, SE2, adjoint_se2)


class SE3Estimator(_EKFBase):
    """Extended Kalman Filter on SE(3)."""

    def __init__(self) -> None:
        super().__init__(6, SE3, adjoint_se3)


class PoseEstimatorNode(BaseNode):
    """Node that estimates pose from twist and pose measurements."""

    GROUP = "estimator"

    def __init__(self, *, config: dict | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}

        mode = str(cfg.get("mode", "SE2")).upper()
        self.twist_topic = cfg.get("twist_topic", "twist")
        self.measure_topic = cfg.get("measure_topic", "pose")
        self.output_topic = cfg.get("output_topic", "pose_estimate")
        self.hz = float(cfg.get("hz", self.hz))

        if mode == "SE3":
            self.estimator = SE3Estimator()
            self._twist_cls = Twist3D
            self._pose_cls = Pose3D
            self._to_group = self._pose3d_to_se3
            self._twist_to_vec = lambda t: np.array([
                t.linear.x,
                t.linear.y,
                t.linear.z,
                t.angular.x,
                t.angular.y,
                t.angular.z,
            ])
        else:
            self.estimator = SE2Estimator()
            self._twist_cls = Twist2D
            self._pose_cls = Pose2D
            self._to_group = self._pose2d_to_se2
            self._twist_to_vec = lambda t: np.array([
                t.linear.x,
                t.linear.y,
                t.angular,
            ])

        self.subscribe(self.twist_topic)
        self.subscribe(self.measure_topic)

        self._last_time = time.time()
        self._last_twist: Optional[object] = None

    def _pose2d_to_se2(self, pose: Pose2D) -> SE2:
        return SE2(SO2.exp(pose.theta), np.array([pose.x, pose.y]))

    def _pose3d_to_se3(self, pose: Pose3D) -> SE3:
        q = GeoQuat(
            x=pose.orientation.x,
            y=pose.orientation.y,
            z=pose.orientation.z,
            w=pose.orientation.w,
        )
        R = SO3.from_quaternion(q)
        return SE3(R, np.array([pose.position.x, pose.position.y, pose.position.z]))

    def step(self) -> None:
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        twist_dict = self.take(self.twist_topic)
        if twist_dict is not None:
            try:
                self._last_twist = self._twist_cls.model_validate(twist_dict)
            except Exception as e:
                logging.debug("Failed to validate twist_dict: %s", e, exc_info=True)

        if self._last_twist is not None:
            self.estimator.propagate(self._twist_to_vec(self._last_twist), dt)

        meas_dict = self.take(self.measure_topic)
        if meas_dict is not None:
            try:
                m = self._pose_cls.model_validate(meas_dict)
                self.estimator.update(self._to_group(m))
            except Exception as e:
                logging.debug("Failed to validate measurement: %s", e, exc_info=True)

        g = self.estimator.pose
        if isinstance(g, SE2):
            pose = Pose2D(x=g.translation[0], y=g.translation[1], theta=g.rotation.theta)
        else:
            q = g.rotation.to_quaternion()
            pose = Pose3D(
                position={"x": g.translation[0], "y": g.translation[1], "z": g.translation[2]},
                orientation={"x": q.x, "y": q.y, "z": q.z, "w": q.w},
            )
        self.put(self.output_topic, to_zenoh_value(pose))

