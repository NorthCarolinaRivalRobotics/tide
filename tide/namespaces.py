from enum import Enum
from typing import Type, Dict

from tide.models import (
    Twist2D,
    Pose2D,
    Pose3D,
    Vector3,
    LaserScan,
    Image,
)


class Group(str, Enum):
    """Reserved top-level groups."""

    CMD = "cmd"
    STATE = "state"
    SENSOR = "sensor"
    MANIPULATOR = "manipulator"


class CmdTopic(str, Enum):
    """Reserved command topics."""

    TWIST = "cmd/twist"
    POSE2D = "cmd/pose2d"
    POSE3D = "cmd/pose3d"


CMD_TYPES: Dict[CmdTopic, Type] = {
    CmdTopic.TWIST: Twist2D,
    CmdTopic.POSE2D: Pose2D,
    CmdTopic.POSE3D: Pose3D,
}


class StateTopic(str, Enum):
    """Reserved state topics."""

    POSE2D = "state/pose2d"
    POSE3D = "state/pose3d"
    TWIST = "state/twist"


STATE_TYPES: Dict[StateTopic, Type] = {
    StateTopic.POSE2D: Pose2D,
    StateTopic.POSE3D: Pose3D,
    StateTopic.TWIST: Twist2D,
}


class SensorTopic(str, Enum):
    """Reserved sensor topics."""

    LIDAR_SCAN = "sensor/lidar/scan"
    IMU_ACCEL = "sensor/imu/accel"


SENSOR_TYPES: Dict[SensorTopic, Type] = {
    SensorTopic.LIDAR_SCAN: LaserScan,
    SensorTopic.IMU_ACCEL: Vector3,
}


def sensor_camera_rgb(camera_id: str) -> str:
    """Return the RGB camera topic for the given camera id."""
    return f"sensor/camera/{camera_id}/rgb"


def sensor_camera_depth(camera_id: str) -> str:
    """Return the depth camera topic for the given camera id."""
    return f"sensor/camera/{camera_id}/depth"


def robot_topic(robot_id: str, topic: str) -> str:
    """Return an absolute topic in the form ``/{robot_id}/{topic}``."""
    topic = topic.lstrip("/")
    return f"/{robot_id}/{topic}"


__all__ = [
    "Group",
    "CmdTopic",
    "StateTopic",
    "SensorTopic",
    "CMD_TYPES",
    "STATE_TYPES",
    "SENSOR_TYPES",
    "sensor_camera_rgb",
    "sensor_camera_depth",
    "robot_topic",
]
