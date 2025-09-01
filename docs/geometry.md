# Geometry Utilities

Tide ships with a lightweight Lie group library covering `SO2`, `SO3`, `SE2` and `SE3` along with helpers like `adjoint_se2`
 and `adjoint_se3`. These classes make it easy to compose poses, integrate twists, and move between frames.

## Field Relative Driving

Operators often command velocities relative to the field. Convert them to body coordinates before sending to the drivetrain:

```python
import numpy as np
from tide.core.geometry import SE2, adjoint_se2

pose_field_robot = SE2.exp(np.array([5.0, 2.0, np.pi / 2]))  # robot pose in the field
field_twist = np.array([1.0, 0.0, 0.0])                      # drive toward +x of the field
body_twist = adjoint_se2(pose_field_robot.inverse()) @ field_twist
```

`body_twist` contains the velocity expressed in the robot frame and can be passed directly to the drivetrain.

## Odometry Using Twist Exponentials

Integrate incremental twists with the `SE2` exponential to propagate pose estimates:

```python
import numpy as np
from tide.core.geometry import SE2

pose = SE2.exp(np.zeros(3))
dt = 0.02
for twist in measurements:  # each twist is [vx, vy, omega] in the body frame
    pose = pose * SE2.exp(twist * dt)
```

## Dynamics Compensation via Log Map

The group logarithm provides an error in tangent space that is useful for second-order drivetrain compensation:

```python
desired = SE2.exp(np.array([2.0, 1.0, 0.0]))
error_twist = (pose.inverse() * desired).log()
# feed error_twist to a controller
```

## Robot → Camera → AprilTag Transformation

Chain `SE3` transforms to move between robot, camera, and tag frames:

```python
import numpy as np
from tide.core.geometry import SE3

robot_to_cam = SE3.exp(np.array([0.0, 0.0, 0.2, 0.0, 0.0, 0.0]))     # camera 20 cm above robot
cam_to_tag = SE3.exp(np.array([1.0, 0.1, 2.0, 0.0, 0.0, np.pi / 2]))  # detection result
robot_to_tag = robot_to_cam * cam_to_tag
position = robot_to_tag.translation
```

`position` is the tag location expressed in the robot frame; additional chaining can extend this to world coordinates.
