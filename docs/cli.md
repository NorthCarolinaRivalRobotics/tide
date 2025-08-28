# Tide CLI Documentation

The Tide CLI provides a set of commands to help you create, run, and manage Tide robotics projects.

## Table of Contents

- [Installation](#installation)
- [Commands](#commands)
  - [init](#init-command)
  - [up](#up-command)
  - [status](#status-command)
- [Project Structure](#project-structure)
- [Example Workflows](#example-workflows)
  - [Creating and Running a Basic Project](#creating-and-running-a-basic-project)
  - [Multi-Robot Configuration](#multi-robot-configuration)
  - [Custom Node Development](#custom-node-development)
  - [Adding Tide to an Existing Project](#adding-tide-to-an-existing-project)

## Installation

Install Tide using pip:

```bash
pip install tide-sdk
```

Or with uv (recommended):

```bash
uv add tide-sdk
```

## Commands

### `init` Command

The `init` command creates a new Tide project with the necessary structure and example nodes.

```bash
tide init [project_name] [options]
```

#### Options

- `--robot-id ROBOT_ID`: Specify the default robot ID (default: "myrobot")
- `--force`: Overwrite existing project if it exists

#### Examples

Create a project with the default robot ID:

```bash
tide init my_robot_project
```

Create a project with a custom robot ID:

```bash
tide init delivery_bot --robot-id delivery1
```

Force overwrite an existing project:

```bash
tide init my_robot_project --force
```


### `up` Command

The `up` command runs a Tide project by launching the nodes specified in the configuration file.

```bash
tide up [options]
```

#### Options

- `--config CONFIG`: Path to configuration file (default: "config/config.yaml")

#### Examples

Run with the default configuration:

```bash
tide up
```

Run with a custom configuration:

```bash
tide up --config custom_config.yaml
```

### `status` Command

The `status` command discovers and displays information about running Tide nodes
on the network. Discovery now queries all groups (`*/*/*`), so even nodes that
only publish custom topics like the ping-pong example will be listed.

```bash
tide status [options]
```

#### Options

- `--timeout TIMEOUT`: Discovery timeout in seconds (default: 2.0)

#### Examples

Quick discovery:

```bash
tide status
```

Extended discovery time:

```bash
tide status --timeout 5.0
```

## Project Structure

When you create a new project with `tide init`, it generates the following structure:

```
my_robot_project/
├── config/
│   └── config.yaml     # Configuration for nodes
├── nodes/
│   ├── robot_node.py   # Main robot control node
│   ├── teleop_node.py  # Node for commanding the robot
│   └── monitor_node.py # Node for monitoring state
├── README.md           # Project documentation
└── requirements.txt    # Dependencies
```

### config/config.yaml

This is where you define your node configuration:

```yaml
session:
  mode: peer  # Mesh network

nodes:
  - type: nodes.robot_node.RobotNode
    params:
      robot_id: "robot1"
      
  - type: nodes.teleop_node.TeleopNode
    params:
      robot_id: "robot1"
      command_rate: 1.0
      
  - type: nodes.monitor_node.MonitorNode
    params:
      robot_id: "robot1"
```

See [config_spec.md](config_spec.md) for a full description of the configuration format.

### nodes/

This directory contains your node implementations:

- `robot_node.py`: The main robot control node that handles commands and publishes state
- `teleop_node.py`: A node for generating commands to control the robot
- `monitor_node.py`: A node for monitoring the robot state

## Example Workflows

### Creating and Running a Basic Project

1. Create a new project:

```bash
tide init my_first_robot --robot-id bot1
```

2. Navigate to the project directory:

```bash
cd my_first_robot
```

3. Install dependencies:

```bash
uv add -r requirements.txt
```

4. Run the project:

```bash
tide up
```

5. In another terminal, check node status:

```bash
tide status
```

### Multi-Robot Configuration

You can modify the config.yaml to work with multiple robots:

```yaml
session:
  mode: peer

nodes:
  # First robot
  - type: nodes.robot_node.RobotNode
    params:
      robot_id: "robot1"
      
  - type: nodes.teleop_node.TeleopNode
    params:
      robot_id: "robot1"
      
  - type: nodes.monitor_node.MonitorNode
    params:
      robot_id: "robot1"
      
  # Second robot
  - type: nodes.robot_node.RobotNode
    params:
      robot_id: "robot2"
      
  - type: nodes.teleop_node.TeleopNode
    params:
      robot_id: "robot2"
      command_rate: 0.5
      
  - type: nodes.monitor_node.MonitorNode
    params:
      robot_id: "robot2"
```

### Adding Tide to an Existing Project

If you have an existing Python project and want to add Tide functionality:

1. Install Tide:

```bash
uv add tide-sdk
```

2. Create a default configuration file by generating a template project and copying its `config/config.yaml`.

3. Create your own Tide nodes or use the templates as a reference:

```bash
# Create a template project separately to use as reference
tide init tide_templates
```

4. Integrate the Tide node launching in your existing code:

```python
from tide.core.utils import launch_from_config
from tide.config import load_config

def start_tide_nodes():
    # Load Tide configuration
    config = load_config("config/tide_config.yaml")

    # Launch Tide nodes and scripts
    nodes, processes = launch_from_config(config)
    return nodes, processes
```

### Custom Node Development

1. Create a new sensor node in your project:

```python
#!/usr/bin/env python3
"""
Example sensor node that publishes simulated data.
"""
import time
import random
from datetime import datetime

from tide.core.node import BaseNode
from tide.models.common import LaserScan, Vector3
from tide.models.serialization import to_zenoh_value
from tide import SensorTopic

class SensorNode(BaseNode):
    """
    Node that publishes simulated sensor data.
    """
    ROBOT_ID = "robot1"  # Robot's unique ID
    GROUP = "sensor"     # Group for this node's topics
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Configuration
        self.update_rate = 10.0  # Hz
        if config and "update_rate" in config:
            self.update_rate = config["update_rate"]
            
        # Override default update rate
        self.hz = self.update_rate
        
        print(f"SensorNode started for robot {self.ROBOT_ID}")
    
    def step(self):
        """Publish simulated sensor data."""
        # Create simulated laser scan data
        num_points = 100
        ranges = [random.uniform(0.5, 10.0) for _ in range(num_points)]
        
        # Create LaserScan message
        scan = LaserScan(
            angle_min=-3.14159 / 2,
            angle_max=3.14159 / 2,
            angle_increment=3.14159 / num_points,
            range_min=0.1,
            range_max=20.0,
            ranges=ranges,
        )
        
        # Publish scan data
        self.put(SensorTopic.LIDAR_SCAN.value, to_zenoh_value(scan))
        
        # Also publish a simple acceleration
        accel = Vector3(
            x=random.uniform(-0.5, 0.5),
            y=random.uniform(-0.5, 0.5),
            z=9.8 + random.uniform(-0.1, 0.1)
        )
        
        self.put(SensorTopic.IMU_ACCEL.value, to_zenoh_value(accel))
```

2. Add the sensor node to your configuration:

```yaml
nodes:
  # ... existing nodes
  
  - type: nodes.sensor_node.SensorNode
    params:
      robot_id: "robot1"
      update_rate: 10.0
``` 
