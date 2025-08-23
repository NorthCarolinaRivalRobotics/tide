# Tide

A lightweight, strongly-typed framework for robotics based on [Zenoh](https://zenoh.io/), with opinionated namespacing.

## Overview

Tide wraps Zenoh's key/value-based pub-sub-query model in a set of strongly-typed "robot nodes," each running in its own thread that talks over a shared Zenoh session.

The framework enforces an opinionated namespacing pattern:

```
/{robot_id}/{group}/{topic}
```

For example:
- `/frogbot/cmd/twist` - Command velocity for the "frogbot" robot
- `/frogbot/state/pose2d` - 2D pose state for the robot
- `/frogbot/sensor/lidar` - Lidar data from the robot
See [docs/namespacing.md](docs/namespacing.md) for a full list of reserved namespaces.  The `tide.namespaces` module exposes enums for these topics so you don't have to hardcode strings.

## Features

- **Opinionated namespacing**: Clear, consistent naming pattern for all messages
- **Zero-config networking**: Lean on Zenoh's peer discovery for automatic device connection
- **Strongly-typed messages**: Uses Pydantic models for validation and serialization
- **Pythonic, thread-based architecture**: Each node runs in its own thread to keep latency low
- **Callback-based**: Register callbacks for specific topics
- **Command-line interface**: Easily create and manage Tide projects

## Installation

```bash
pip install tide-sdk
```

Or with uv (recommended):

```bash
uv add tide-sdk
```

## Command-Line Interface

Tide comes with a powerful CLI to help you create and manage projects.

### Creating a New Project

```bash
tide init my_robot_project --robot-id robot1
```

This creates a new project directory with the following structure:

```
my_robot_project/
├── config/
│   └── config.yaml     # Configuration for nodes
├── nodes/
│   ├── robot_node.py   # Main robot control node
│   ├── teleop_node.py  # Node for commanding the robot
│   └── monitor_node.py # Node for monitoring state
├── main.py             # Project entry point
├── README.md           # Project documentation
└── requirements.txt    # Dependencies
```

### Running Your Project

To start your Tide project:

```bash
cd my_robot_project
tide up
```

This will:
1. Load the configuration from `config/config.yaml`
2. Start all the defined nodes
3. Display a table of running nodes

You can specify a custom configuration file:

```bash
tide up --config path/to/custom_config.yaml
```

### Checking Node Status

To discover running Tide nodes on the network:

```bash
tide status
```

This shows a list of all discovered Tide nodes. The discovery uses the
`*/*/*` wildcard so custom groups like the ping-pong example are also found.
The output includes:
- Robot ID
- Group
- Topic

For longer discovery times:

```bash
tide status --timeout 5.0
```

## Programming API

### Defining a Node

```python
from tide.core.node import BaseNode
from tide.models import Twist2D, Pose2D, to_zenoh_value
from tide import CmdTopic, StateTopic

class MyRobotNode(BaseNode):
    ROBOT_ID = "myrobot"  # Your robot's unique ID
    GROUP = "controller"  # Group for this node
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Subscribe to command velocity using the reserved enum
        self.subscribe(CmdTopic.TWIST.value, self._on_cmd_vel)
    
    def _on_cmd_vel(self, data):
        # Process command velocity message
        # ...
    
    def step(self):
        # Called at the node's update rate
        # Publish robot state
        pose = Pose2D(x=1.0, y=2.0, theta=0.5)
        self.put(StateTopic.POSE2D.value, to_zenoh_value(pose))
```

### Launching Nodes

```python
import time
from tide.core.utils import launch_from_config
from tide.config import load_config

def main():
    # Load configuration
    config = load_config('config.yaml')

    # Launch nodes
    nodes = launch_from_config(config)

    try:
        print(f"Started {len(nodes)} nodes. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by user")
        for node in nodes:
            node.stop()

if __name__ == "__main__":
    main()
```

### Configuration File

```yaml
session:
  mode: peer  # Mesh network

nodes:
  - type: my_package.MyRobotNode
    params:
      robot_id: "robot1"
      
  - type: my_package.TeleopNode
    params:
      robot_id: "robot1"
```

See `docs/config_spec.md` for the formal configuration specification.

## Complete Example

The generated project template includes a complete working example. Here's how the nodes work together:

1. **TeleopNode** - Generates simple oscillating motion commands (simulating joystick)
   ```python
   def step(self):
       # Create sinusoidal motion pattern
       t = time.time()
       self.linear_vel = 0.5 * math.sin(0.2 * t)
       self.angular_vel = 0.2 * math.cos(0.1 * t)

       # Create and publish the command
       cmd = Twist2D(
           linear=Vector2(x=self.linear_vel),
           angular=self.angular_vel
       )
       self.put(CmdTopic.TWIST.value, to_zenoh_value(cmd))
   ```

2. **RobotNode** - Receives commands and simulates robot movement
   ```python
   def _on_cmd_vel(self, data):
       cmd = from_zenoh_value(data, Twist2D)
       self.linear_vel = cmd.linear.x
       self.angular_vel = cmd.angular
   
   def step(self):
       # Simple motion model - integrate velocity
       dt = time.time() - self.last_update
       self.theta += self.angular_vel * dt
       self.x += self.linear_vel * math.cos(self.theta) * dt
       self.y += self.linear_vel * math.sin(self.theta) * dt

       # Publish the current pose
       pose = Pose2D(x=self.x, y=self.y, theta=self.theta)
       self.put(StateTopic.POSE2D.value, to_zenoh_value(pose))
   ```

3. **MonitorNode** - Displays the robot's state
   ```python
   def _on_pose(self, data):
       pose = from_zenoh_value(data, Pose2D)
       print(f"Robot pose: x={pose.x:.2f}, y={pose.y:.2f}, theta={pose.theta:.2f}")
   ```

This demonstrates:
- Opinionated topic naming (`cmd/twist`, `state/pose2d`)
- Callback-based architecture for handling messages
- Strong typing with Pydantic models
- Serialization/deserialization with Zenoh

## Common Message Types

- **Twist2D**: 2D velocity command (linear x, y and angular z)
- **Pose2D**: 2D pose (x, y, theta)
- **Pose3D**: 3D pose (position and orientation)
- **Acceleration3D**: 3D acceleration (linear and angular)
- **LaserScan**: 2D laser scan data

## Built-in Nodes

Tide ships with a small library of reusable nodes.  `PIDNode` implements a
basic PID controller that reads a state and reference value and publishes a
command.  `WebcamNode` captures frames from a V4L2 webcam and publishes raw
images.  See [docs/pid_node.md](docs/pid_node.md) and
[docs/webcam_node.md](docs/webcam_node.md) for configuration details.

## License

MIT
