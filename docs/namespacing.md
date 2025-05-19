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
Users are free to create additional groups and topics as needed.

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

## Custom Groups

Groups other than the ones listed above are unreserved. Examples used in
the project include `teleop`, `monitor`, `processor`, and `visualization`.
These can be freely defined to organize application-specific messages.

## Discovering Topics

Because all topics share the same `{robot_id}/{group}/{topic}` pattern,
utilities can discover information with wildcards. For example, querying
`*/state/*` finds all state topics for all robots.

