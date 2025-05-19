"""
tide - A Zenoh-based framework for robotics with opinionated namespacing

This framework provides a lightweight, strongly-typed layer
on top of Zenoh for building robot control systems.
"""

__version__ = "0.1.0"

# Import core components
from tide.core.node import BaseNode

# Reserved namespace enums and helpers
from tide.namespaces import (
    Group,
    CmdTopic,
    StateTopic,
    SensorTopic,
    sensor_camera_rgb,
    sensor_camera_depth,
)

__all__ = [
    "BaseNode",
    "Group",
    "CmdTopic",
    "StateTopic",
    "SensorTopic",
    "sensor_camera_rgb",
    "sensor_camera_depth",
]
