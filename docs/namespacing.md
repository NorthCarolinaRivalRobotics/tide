# Tide Namespacing Reference

Tide uses an opinionated topic format to simplify discovery and
interoperability between nodes:

```
/{robot_id}/{group}/{topic}
```

* **robot_id** – unique name of the robot
* **group** – logical grouping of related topics
* **topic** – specific message name

The following groups and topics are reserved for common functionality.
These top-level groups are represented by the `Group` enum in
`tide.namespaces`. Users are free to create additional groups and topics
as needed.

## Command Topics (`cmd`)

Topics under `cmd` are used to send commands to a robot.

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `cmd/twist` | `Twist2D` | 2D velocity command `{linear:{x,y}, angular, timestamp}` |
| `cmd/pose2d` | `Pose2D`  | Desired 2D pose setpoint |
| `cmd/pose3d` | `Pose3D`  | Desired 3D pose setpoint |

## State Topics (`state`)

Topics under `state` report the current state of a robot.

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `state/pose2d` | `Pose2D` | Current 2D pose `{x,y,theta,timestamp}` |
| `state/pose3d` | `Pose3D` | Current 3D pose |
| `state/twist`  | `Twist2D` or `Twist3D` | Current velocity |

## Sensor Topics (`sensor`)

Sensor data is published under the `sensor` group. Common examples include:

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `sensor/lidar/scan` | `LaserScan` | 2D lidar data |
| `sensor/imu/accel`  | `Vector3`   | IMU acceleration |
| `sensor/imu/quat`   | `Quaternion`| IMU orientation as a quaternion |
| `sensor/imu/gyro_vel` | `Vector3` | IMU angular velocity |
| `sensor/camera/{camera_id}/rgb` | `Image` | RGB image from the named camera |
| `sensor/camera/{camera_id}/depth` | `Image` | Depth image from the named camera |

If a robot has multiple cameras, choose a descriptive `{camera_id}` such as
`front` or `rear` to differentiate sources.

## Manipulator Topics (`manipulator`)

Robots with manipulators (arms, grippers, claws) can use the
`manipulator` group. The namespace is intentionally flexible so
implementations may expose joints or end effectors as topics.

Example:

```
/{robot_id}/manipulator/state/claw
```

The above could publish a custom status object describing the claw
position or whether it is open or closed. Commands may be sent with
`manipulator/cmd/claw` or similar topics.

## Motor Topics (`motors`)

Individual motor control and feedback use the `motors` group with a
numeric motor identifier:

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `motors/{id}/cmd_pos` | `MotorPosition` | Set target position in rotations |
| `motors/{id}/cmd_vel` | `MotorVelocity` | Set target velocity in rotations/sec |
| `motors/{id}/pos` | `MotorPosition` | Current motor position in rotations |
| `motors/{id}/vel` | `MotorVelocity` | Current motor velocity in rotations/sec |

Helper functions in `tide.namespaces` build these topics:

```python
from tide.namespaces import motor_cmd_pos, motor_pos

cmd_key = motor_cmd_pos(1)  # "motors/1/cmd_pos"
state_key = motor_pos(1)    # "motors/1/pos"
```

## Custom Groups

Groups other than the ones listed above are unreserved. Examples used in
the project include `teleop`, `monitor`, `processor`, and `visualization`.
These can be freely defined to organize application-specific messages.

## Discovering Topics

Because all topics share the same `{robot_id}/{group}/{topic}` pattern,
utilities can discover information with wildcards. For example, querying
`*/state/*` finds all state topics for all robots.

## Python Helpers

Tide provides enums representing all reserved groups and topics in `tide.namespaces`. These are also re-exported from the top-level `tide` package for convenience.

```python
from tide import Group, CmdTopic, StateTopic, SensorTopic,
    sensor_camera_rgb, sensor_camera_depth

# Subscribe to a reserved topic using the enum value
self.subscribe(CmdTopic.TWIST.value, self._on_cmd_vel)

# Publish state updates using the enum value
self.put(StateTopic.POSE2D.value, to_zenoh_value(pose))

# Build camera topics dynamically
rgb_key = sensor_camera_rgb("front")
self.put(rgb_key, to_zenoh_value(rgb_image))

# Depth images are supported with a helper as well
depth_key = sensor_camera_depth("front")
self.put(depth_key, to_zenoh_value(depth_image))

# Build a key for another robot
cmd_key = robot_topic("otherbot", CmdTopic.TWIST.value)
z.put(cmd_key, to_zenoh_value(cmd_vel))
```

Mappings such as `CMD_TYPES`, `STATE_TYPES`, and `SENSOR_TYPES` allow lookup of the expected message type for each reserved topic.
