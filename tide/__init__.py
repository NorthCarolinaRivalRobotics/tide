"""
tide - A Zenoh-based framework for robotics with opinionated namespacing

This framework provides a lightweight, strongly-typed layer
on top of Zenoh for building robot control systems.
"""

__version__ = "0.1.12"

# Import core components
from tide.core.node import BaseNode
from tide.components import PIDNode, BehaviorTreeNode

# Reserved namespace enums and helpers
from tide.namespaces import (
    Group,
    CmdTopic,
    StateTopic,
    SensorTopic,
    sensor_camera_rgb,
    sensor_camera_depth,
    motor_cmd_pos,
    motor_cmd_vel,
    motor_pos,
    motor_vel,
    robot_topic,
)

__all__ = [
    "BaseNode",
    "Group",
    "CmdTopic",
    "StateTopic",
    "SensorTopic",
    "sensor_camera_rgb",
    "sensor_camera_depth",
    "motor_cmd_pos",
    "motor_cmd_vel",
    "motor_pos",
    "motor_vel",
    "robot_topic",
    "PIDNode",
    "BehaviorTreeNode",
]
