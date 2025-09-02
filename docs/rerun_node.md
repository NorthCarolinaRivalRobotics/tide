# Rerun Visualization Node

The `RerunNode` provides a convenient way to visualize data from Tide
topics using the [Rerun](https://www.rerun.io) SDK.  The node subscribes
to a set of topics and attempts to infer the message type from the topic
name.  When a known Tide message type is detected, it is displayed with a
sensible default visualization.

## Configuration

```yaml
node: tide.components.rerun_node.RerunNode
config:
  topics:
    - sensor/camera_rgb
    - pose/robot
  spawn: false           # do not launch the native viewer
  robot_size: [0.5, 0.3, 0.2]
```

* `topics`: list of topic paths to subscribe to.
* `spawn`: when `true` (default) the Rerun viewer is launched.
* `robot_size`: default size used when drawing robot poses as 3D boxes.

## Supported message types

The node has built-in logging functions for all Tide message models:

- `Pose2D` and `Pose3D`
- `Twist2D` and `Twist3D`
- `Acceleration3D`
- `Image`
- `LaserScan`
- `OccupancyGrid2D`
- `MotorPosition` and `MotorVelocity`

Each logging function is implemented independently to make the system
maintainable and extensible.

## Extending

To support a custom message type or override the visualization, create a
new logging function and register it in the `_LOGGERS` mapping:

```python
from tide.components.rerun_node import _LOGGERS
from my_models import MyMessage


def log_my_message(path: str, msg: MyMessage) -> None:
    # custom Rerun drawing code
    ...

_LOGGERS[MyMessage] = log_my_message
```

Alternatively, users can subclass `RerunNode` and override `_guess_type`
or `_on_msg` to plug in application-specific logic.
