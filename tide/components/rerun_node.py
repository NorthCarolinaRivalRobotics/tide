"""Rerun visualization node for Tide topics."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Type

import numpy as np

import rerun as rr

from tide.core.node import BaseNode
from tide.models.common import (
    Acceleration3D,
    Image,
    LaserScan,
    MotorPosition,
    MotorVelocity,
    OccupancyGrid2D,
    Pose2D,
    Pose3D,
    Twist2D,
    Twist3D,
)


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _log_pose2d(path: str, msg: Pose2D, *, size: tuple[float, float] = (0.5, 0.3)) -> None:
    """Log a 2D pose as a 3D box with a heading arrow."""
    x, y, theta = msg.x, msg.y, msg.theta
    rr.log(
        path,
        rr.Boxes3D(
            centers=[[x, y, 0.0]],
            half_sizes=[[size[0] / 2.0, size[1] / 2.0, 0.05]],
        ),
    )
    rr.log(
        f"{path}/heading",
        rr.Arrows3D(
            origins=[[x, y, 0.0]],
            vectors=[[np.cos(theta), np.sin(theta), 0.0]],
        ),
    )


def _log_pose3d(path: str, msg: Pose3D, *, size: tuple[float, float, float] = (0.5, 0.3, 0.2)) -> None:
    pos = msg.position
    rr.log(
        path,
        rr.Boxes3D(
            centers=[[pos.x, pos.y, pos.z]],
            half_sizes=[[size[0] / 2.0, size[1] / 2.0, size[2] / 2.0]],
        ),
    )


def _log_twist(path: str, linear: Iterable[float], *, origin: Iterable[float] | None = None) -> None:
    origin = origin or (0.0, 0.0, 0.0)
    rr.log(
        path,
        rr.Arrows3D(
            origins=[list(origin)],
            vectors=[list(linear)],
        ),
    )


def _log_twist2d(path: str, msg: Twist2D) -> None:
    _log_twist(path, (msg.linear.x, msg.linear.y, 0.0))


def _log_twist3d(path: str, msg: Twist3D) -> None:
    _log_twist(path, (msg.linear.x, msg.linear.y, msg.linear.z))


def _log_accel3d(path: str, msg: Acceleration3D) -> None:
    _log_twist(path, (msg.linear.x, msg.linear.y, msg.linear.z))


def _log_image(path: str, msg: Image) -> None:
    arr = np.frombuffer(msg.data, dtype=np.uint8)
    if msg.encoding.lower() in {"rgb8", "bgr8"}:
        arr = arr.reshape((msg.height, msg.width, 3))
    else:
        arr = arr.reshape((msg.height, msg.width))
    rr.log(path, rr.Image(arr))


def _log_laserscan(path: str, msg: LaserScan) -> None:
    angles = msg.angle_min + np.arange(len(msg.ranges)) * msg.angle_increment
    xs = np.cos(angles) * np.array(msg.ranges)
    ys = np.sin(angles) * np.array(msg.ranges)
    points = np.stack([xs, ys, np.zeros_like(xs)], axis=1)
    rr.log(path, rr.Points3D(points))


def _log_occupancy(path: str, msg: OccupancyGrid2D) -> None:
    data = np.array(msg.data, dtype=np.uint8).reshape((msg.height, msg.width))
    rr.log(path, rr.Image(data))


def _log_motor_position(path: str, msg: MotorPosition) -> None:
    rr.log(path, rr.Scalar(msg.rotations))


def _log_motor_velocity(path: str, msg: MotorVelocity) -> None:
    rr.log(path, rr.Scalar(msg.rotations_per_sec))


# Mapping from types to logger functions
_LOGGERS: Dict[Type[Any], Callable[[str, Any], None]] = {
    Pose2D: _log_pose2d,
    Pose3D: _log_pose3d,
    Twist2D: _log_twist2d,
    Twist3D: _log_twist3d,
    Acceleration3D: _log_accel3d,
    Image: _log_image,
    LaserScan: _log_laserscan,
    OccupancyGrid2D: _log_occupancy,
    MotorPosition: _log_motor_position,
    MotorVelocity: _log_motor_velocity,
}


# ---------------------------------------------------------------------------
# Node implementation
# ---------------------------------------------------------------------------

class RerunNode(BaseNode):
    """Visualization node using the Rerun SDK."""

    GROUP = "debug"

    def __init__(self, *, config: dict | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}

        rr.init(cfg.get("app_id", "tide_rerun"), spawn=cfg.get("spawn", True))

        self.robot_size = tuple(cfg.get("robot_size", (0.5, 0.3, 0.2)))

        topics = cfg.get("topics", [])
        self._topic_types: Dict[str, Type[Any]] = {}
        for topic in topics:
            ttype = self._guess_type(topic)
            self._topic_types[topic] = ttype
            self.subscribe(topic, lambda msg, t=topic, tp=ttype: self._on_msg(t, tp, msg))

    # ------------------------------------------------------------------
    def _guess_type(self, topic: str) -> Type[Any]:
        t = topic.lower()
        if "image" in t or "camera" in t:
            return Image
        if "pose3" in t:
            return Pose3D
        if "pose" in t:
            return Pose2D
        if "twist3" in t:
            return Twist3D
        if "twist" in t:
            return Twist2D
        if "accel" in t:
            return Acceleration3D
        if "scan" in t:
            return LaserScan
        if "occup" in t or "grid" in t:
            return OccupancyGrid2D
        if "motor" in t:
            if "velocity" in t:
                return MotorVelocity
            if "position" in t:
                return MotorPosition
        return dict

    # ------------------------------------------------------------------
    def _on_msg(self, topic: str, msg_type: Type[Any], data: Dict[str, Any]) -> None:
        if msg_type is dict:
            return
        try:
            msg = msg_type.model_validate(data)
        except (ValueError, TypeError):
            return

        logger = _LOGGERS.get(msg_type)
        if logger is None:
            return

        if msg_type is Pose2D:
            logger(topic, msg, size=self.robot_size[:2])
        elif msg_type is Pose3D:
            logger(topic, msg, size=self.robot_size)
        else:
            logger(topic, msg)

    # ------------------------------------------------------------------
    def step(self) -> None:  # pragma: no cover - passive node
        pass
