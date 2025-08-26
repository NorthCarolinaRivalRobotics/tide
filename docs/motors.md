# Motor Topic Specification

This document describes the reserved Tide topics for controlling and
monitoring individual motors.

## Topic Pattern

```
/{robot_id}/motors/{motor_id}/{suffix}
```

- **robot_id** – name of the robot
- **motor_id** – numeric identifier for the motor
- **suffix** – one of `cmd_pos`, `cmd_vel`, `pos`, `vel`

## Message Types

| Suffix | Model | Description |
|--------|-------|-------------|
| `cmd_pos` / `pos` | `MotorPosition` | Motor position target or state in full rotations |
| `cmd_vel` / `vel` | `MotorVelocity` | Motor velocity target or state in rotations per second |

The models are defined in `tide.models`:

```python
from tide.models import MotorPosition, MotorVelocity

MotorPosition(rotations: float)
MotorVelocity(rotations_per_sec: float)
```

## Examples

```python
from tide.namespaces import motor_cmd_vel
from tide.models import MotorVelocity, to_zenoh_value

key = motor_cmd_vel(1)
msg = MotorVelocity(rotations_per_sec=5.0)
zenoh_session.put(f"/rover/{key}", to_zenoh_value(msg))
```

```python
from tide.namespaces import motor_pos
from tide.models import MotorPosition

# Subscribe to motor position updates for motor 2
key = motor_pos(2)
session.declare_subscriber(f"/rover/{key}", lambda s: ...)
```
