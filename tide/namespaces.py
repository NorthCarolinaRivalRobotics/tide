from enum import Enum
from typing import Type, Dict

from tide.models import (
    Twist2D,
    Pose2D,
    Pose3D,
    Vector3,
    LaserScan,
    Image,
    Quaternion,
)


class Group(str, Enum):
    """Reserved top-level groups."""

    CMD = "cmd"
    STATE = "state"
    SENSOR = "sensor"
    MANIPULATOR = "manipulator"
    ROBOT = "robot"


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


class RobotTopic(str, Enum):
    """Reserved robot topics."""

    ORIENTATION_QUAT = "robot/orientation/quat"


ROBOT_TYPES: Dict[RobotTopic, Type] = {
    RobotTopic.ORIENTATION_QUAT: Quaternion,
}


def sensor_camera_rgb(camera_id: str) -> str:
    """Return the RGB camera topic for the given camera id."""
    return f"sensor/camera/{camera_id}/rgb"


def sensor_camera_depth(camera_id: str) -> str:
    """Return the depth camera topic for the given camera id."""
    return f"sensor/camera/{camera_id}/depth"


def motor_cmd_pos(motor_id: int) -> str:
    """Topic for commanding a motor position in rotations."""
    return f"motors/{motor_id}/cmd_pos"


def motor_cmd_vel(motor_id: int) -> str:
    """Topic for commanding a motor velocity in rotations/sec."""
    return f"motors/{motor_id}/cmd_vel"


def motor_pos(motor_id: int) -> str:
    """Topic publishing a motor's current position in rotations."""
    return f"motors/{motor_id}/pos"


def motor_vel(motor_id: int) -> str:
    """Topic publishing a motor's current velocity in rotations/sec."""
    return f"motors/{motor_id}/vel"


def robot_topic(robot_id: str, topic: str) -> str:
    """Return an absolute topic in the form ``/{robot_id}/{topic}``."""
    topic = topic.lstrip("/")
    return f"/{robot_id}/{topic}"


__all__ = [
    "Group",
    "CmdTopic",
    "StateTopic",
    "SensorTopic",
    "RobotTopic",
    "CMD_TYPES",
    "STATE_TYPES",
    "SENSOR_TYPES",
    "ROBOT_TYPES",
    "sensor_camera_rgb",
    "sensor_camera_depth",
    "motor_cmd_pos",
    "motor_cmd_vel",
    "motor_pos",
    "motor_vel",
    "robot_topic",
]
